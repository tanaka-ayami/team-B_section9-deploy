"""
documents.py の残り（GET一覧・絞り込み・GET詳細・DELETE）のテスト。
docker compose exec backend pytest tests/test_documents_extra.py -v で実行確認用。
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document
from app.models.notification import NotificationSchedule
from app.models.user import Group, GroupMember

client = TestClient(app)

NON_EXISTENT_DOCUMENT_ID = uuid.uuid4()


def _make_group_with_member(db_session, owner):
    group = Group(name="documents_extraテスト用グループ", created_by=owner.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=owner.id))
    db_session.commit()
    return group


def test_list_documents_filters_by_has_deadline(user_a, db_session, login_as):
    """has_deadlineクエリパラメータで絞り込みができること（issue #54）。"""
    group = _make_group_with_member(db_session, user_a)

    doc_with_deadline = Document(
        group_id=group.id,
        title="期限ありの書類",
        image_url="https://example.com/a.jpg",
        has_deadline=True,
        created_by=user_a.id,
    )
    doc_without_deadline = Document(
        group_id=group.id,
        title="期限なしの書類",
        image_url="https://example.com/b.jpg",
        has_deadline=False,
        created_by=user_a.id,
    )
    db_session.add(doc_with_deadline)
    db_session.add(doc_without_deadline)
    db_session.commit()

    with login_as(user_a):
        res = client.get(
            f"/v1/groups/{group.id}/documents", params={"has_deadline": "false"}
        )

    assert res.status_code == 200
    titles = [d["title"] for d in res.json()["documents"]]
    assert "期限なしの書類" in titles
    assert "期限ありの書類" not in titles

    # cleanup
    db_session.query(Document).filter(
        Document.id.in_([doc_with_deadline.id, doc_without_deadline.id])
    ).delete(synchronize_session=False)
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_list_documents_forbidden_for_non_member(user_a, user_b, db_session, login_as):
    """グループのメンバーでなければ一覧取得できず403になること。"""
    group = _make_group_with_member(db_session, user_a)

    with login_as(user_b):
        res = client.get(f"/v1/groups/{group.id}/documents")

    assert res.status_code == 403

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_get_document_not_found_returns_404(user_a, login_as):
    """存在しない書類IDの詳細取得は404になること。"""
    with login_as(user_a):
        res = client.get(f"/v1/documents/{NON_EXISTENT_DOCUMENT_ID}")

    assert res.status_code == 404


def test_get_document_forbidden_for_non_member(user_a, user_b, db_session, login_as):
    """グループのメンバーでなければ詳細取得できず403になること。"""
    group = _make_group_with_member(db_session, user_a)
    document = Document(
        group_id=group.id,
        title="詳細取得テスト書類",
        image_url="https://example.com/c.jpg",
        has_deadline=False,
        created_by=user_a.id,
    )
    db_session.add(document)
    db_session.commit()

    with login_as(user_b):
        res = client.get(f"/v1/documents/{document.id}")

    assert res.status_code == 403

    # cleanup
    db_session.query(Document).filter(Document.id == document.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_delete_document_removes_document_and_cancels_reminders(
    user_a, db_session, login_as
):
    """
    書類を削除すると、書類自体が削除され、紐づくpendingのリマインドも
    cancelledへ更新されること。
    """
    from datetime import date, timedelta

    group = _make_group_with_member(db_session, user_a)

    deadline = (date.today() + timedelta(days=7)).isoformat()

    with login_as(user_a):
        create_res = client.post(
            "/v1/documents",
            json={
                "group_id": str(group.id),
                "title": "削除テスト書類",
                "image_url": "https://example.com/d.jpg",
                "has_deadline": True,
                "deadline_date": deadline,
            },
        )
    document_id = create_res.json()["id"]

    with login_as(user_a):
        res = client.delete(f"/v1/documents/{document_id}")

    assert res.status_code == 204

    remaining_document = (
        db_session.query(Document).filter(Document.id == document_id).first()
    )
    assert remaining_document is None

    remaining_pending = (
        db_session.query(NotificationSchedule)
        .filter(
            NotificationSchedule.document_id == document_id,
            NotificationSchedule.status == "pending",
        )
        .count()
    )
    assert remaining_pending == 0

    # cleanup（NotificationScheduleはON DELETE CASCADEで既に消えているはずだが念のため）
    db_session.query(NotificationSchedule).filter(
        NotificationSchedule.document_id == document_id
    ).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_delete_document_not_found_returns_404(user_a, login_as):
    """存在しない書類の削除は404になること。"""
    with login_as(user_a):
        res = client.delete(f"/v1/documents/{NON_EXISTENT_DOCUMENT_ID}")

    assert res.status_code == 404