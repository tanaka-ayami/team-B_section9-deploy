"""
書類スキャンAPI（monthly_scan_countの増分ロジック）のテスト。
docker compose exec backend pytest tests/test_documents.py -v で実行確認用。

方針：
- OpenAI（analyze_document_image）・Cloudinary（upload_document_image）は
  実際に外部通信させず、unittest.mock.patchで差し替える。
- monthly_scan_countはテストごとに明示的にセットし、cleanupで元の値に戻す。
- login_asが渡すuserオブジェクトはテスト側のdb_sessionに紐づくため、
  検証にはrefresh()ではなくcommit()を使う
  （エンドポイント側の別セッションでのcommitとは別物のため、
  refresh()だと変更が見えないことがある）。
"""
from datetime import date, timedelta
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document
from app.models.notification import AppNotification, NotificationSchedule
from app.models.user import Group, GroupMember
from app.schemas.document_analysis import DocumentAnalysis

client = TestClient(app)


def _dummy_file():
    """テスト用のダミー画像ファイル（中身は空でよい。upload自体をモックするため）。"""
    return {"file": ("test.jpg", BytesIO(b"dummy image bytes"), "image/jpeg")}


def test_scan_success_increments_scan_count(user_a, db_session, login_as):
    """解析成功時、monthly_scan_countが+1されること。"""
    user_a.monthly_scan_count = 0
    db_session.commit()

    fake_analysis = DocumentAnalysis(
        title="遠足のお知らせ",
        category="学校",
        deadline="2026-07-01",
        has_deadline=True,
    )

    with login_as(user_a):
        with patch(
            "app.api.v1.documents.upload_document_image",
            return_value={"image_url": "https://example.com/dummy.jpg"},
        ), patch(
            "app.api.v1.documents.analyze_document_image",
            return_value=fake_analysis,
        ):
            res = client.post("/v1/documents/scan", files=_dummy_file())

    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "遠足のお知らせ"

    db_session.commit()
    assert user_a.monthly_scan_count == 1

    # cleanup
    user_a.monthly_scan_count = 0
    db_session.commit()


def test_scan_failure_does_not_increment_scan_count(user_a, db_session, login_as):
    """解析失敗時、monthly_scan_countは増えないこと（無料枠を消費させない）。"""
    user_a.monthly_scan_count = 0
    db_session.commit()

    with login_as(user_a):
        with patch(
            "app.api.v1.documents.upload_document_image",
            return_value={"image_url": "https://example.com/dummy.jpg"},
        ), patch(
            "app.api.v1.documents.analyze_document_image",
            return_value=None,
        ):
            res = client.post("/v1/documents/scan", files=_dummy_file())

    assert res.status_code == 200
    body = res.json()
    assert body["title"] is None

    db_session.commit()
    assert user_a.monthly_scan_count == 0

    # cleanup（増えていない想定だが、念のため明示的にリセット）
    user_a.monthly_scan_count = 0
    db_session.commit()


def test_scan_limit_exceeded_returns_422(user_a, db_session, login_as):
    """上限（30枚）到達時、422を返し、Cloudinary/OpenAIを呼び出さないこと。"""
    user_a.monthly_scan_count = 30
    db_session.commit()

    with login_as(user_a):
        with patch(
            "app.api.v1.documents.upload_document_image",
        ) as mock_upload, patch(
            "app.api.v1.documents.analyze_document_image",
        ) as mock_analyze:
            res = client.post("/v1/documents/scan", files=_dummy_file())

    assert res.status_code == 422

    # 上限チェックは解析前に行われ、無駄な外部API呼び出しが発生していないこと
    mock_upload.assert_not_called()
    mock_analyze.assert_not_called()

    db_session.commit()
    assert user_a.monthly_scan_count == 30

    # cleanup
    user_a.monthly_scan_count = 0
    db_session.commit()


def test_create_document_notifies_other_members_but_not_self(
    user_a, user_b, db_session, login_as
):
    """
    書類登録時、登録した本人（user_a）には通知が作られず、
    同じグループの他メンバー（user_b）には作られること（FR-009）。
    has_deadline=true かつ deadline_date ありの場合、
    NotificationScheduleが全メンバー分作られること。
    """
    group = Group(name="通知テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.add(GroupMember(group_id=group.id, user_id=user_b.id))
    db_session.commit()

    deadline = (date.today() + timedelta(days=7)).isoformat()

    with login_as(user_a):
        res = client.post(
            "/v1/documents",
            json={
                "group_id": str(group.id),
                "title": "テスト書類",
                "image_url": "https://example.com/dummy.jpg",
                "has_deadline": True,
                "deadline_date": deadline,
            },
        )

    assert res.status_code == 201
    document_id = res.json()["id"]

    notifications = (
        db_session.query(AppNotification)
        .filter(AppNotification.document_id == document_id)
        .all()
    )
    notified_user_ids = {str(n.user_id) for n in notifications}

    assert str(user_a.id) not in notified_user_ids
    assert str(user_b.id) in notified_user_ids

    schedules = (
        db_session.query(NotificationSchedule)
        .filter(NotificationSchedule.document_id == document_id)
        .all()
    )
    schedule_user_ids = {str(s.user_id) for s in schedules}

    assert str(user_a.id) in schedule_user_ids
    assert str(user_b.id) in schedule_user_ids

    # cleanup
    db_session.query(NotificationSchedule).filter(
        NotificationSchedule.document_id == document_id
    ).delete()
    db_session.query(AppNotification).filter(
        AppNotification.document_id == document_id
    ).delete()
    db_session.query(Document).filter(Document.id == document_id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_mark_document_done_cancels_pending_reminders(user_a, db_session, login_as):
    """
    is_done=trueへの更新時、その書類に紐づくpending状態の
    NotificationScheduleがすべてcancelledへ一括更新されること（FR-006）。
    """
    group = Group(name="済スタンプテスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    deadline = (date.today() + timedelta(days=7)).isoformat()

    with login_as(user_a):
        create_res = client.post(
            "/v1/documents",
            json={
                "group_id": str(group.id),
                "title": "済スタンプテスト書類",
                "image_url": "https://example.com/dummy.jpg",
                "has_deadline": True,
                "deadline_date": deadline,
            },
        )
    document_id = create_res.json()["id"]

    # 登録直後はpending状態のはず
    pending_before = (
        db_session.query(NotificationSchedule)
        .filter(
            NotificationSchedule.document_id == document_id,
            NotificationSchedule.status == "pending",
        )
        .count()
    )
    assert pending_before > 0

    with login_as(user_a):
        patch_res = client.patch(
            f"/v1/documents/{document_id}",
            json={"is_done": True},
        )

    assert patch_res.status_code == 200
    assert patch_res.json()["is_done"] is True

    remaining_pending = (
        db_session.query(NotificationSchedule)
        .filter(
            NotificationSchedule.document_id == document_id,
            NotificationSchedule.status == "pending",
        )
        .count()
    )
    assert remaining_pending == 0

    cancelled_count = (
        db_session.query(NotificationSchedule)
        .filter(
            NotificationSchedule.document_id == document_id,
            NotificationSchedule.status == "cancelled",
        )
        .count()
    )
    assert cancelled_count == pending_before

    # cleanup
    db_session.query(NotificationSchedule).filter(
        NotificationSchedule.document_id == document_id
    ).delete()
    db_session.query(AppNotification).filter(
        AppNotification.document_id == document_id
    ).delete()
    db_session.query(Document).filter(Document.id == document_id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_update_document_forbidden_for_non_member(user_a, user_b, db_session, login_as):
    """グループのメンバーでないユーザーはPATCHできず403になること。"""
    group = Group(name="権限テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    with login_as(user_a):
        create_res = client.post(
            "/v1/documents",
            json={
                "group_id": str(group.id),
                "title": "権限テスト書類",
                "image_url": "https://example.com/dummy.jpg",
                "has_deadline": False,
            },
        )
    document_id = create_res.json()["id"]

    # user_bはこのグループのメンバーではない
    with login_as(user_b):
        patch_res = client.patch(
            f"/v1/documents/{document_id}",
            json={"is_done": True},
        )

    assert patch_res.status_code == 403

    # cleanup
    db_session.query(Document).filter(Document.id == document_id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()
    