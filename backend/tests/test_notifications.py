"""
アプリ内お知らせAPI（GET /v1/notifications、PATCH /v1/notifications/{id}/read）のテスト。
docker compose exec backend pytest tests/test_notifications.py -v で実行確認用。
"""
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document
from app.models.notification import AppNotification
from app.models.user import Group, GroupMember

client = TestClient(app)


def _make_group_and_document(db_session, owner):
    group = Group(name="通知APIテスト用グループ", created_by=owner.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=owner.id))

    document = Document(
        group_id=group.id,
        title="通知APIテスト書類",
        image_url="https://example.com/dummy.jpg",
        has_deadline=False,
        created_by=owner.id,
    )
    db_session.add(document)
    db_session.flush()
    db_session.commit()
    return group, document


def _cleanup(db_session, group, document, notification_ids):
    db_session.query(AppNotification).filter(
        AppNotification.id.in_(notification_ids)
    ).delete(synchronize_session=False)
    db_session.query(Document).filter(Document.id == document.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_get_notifications_returns_only_own_sorted_desc(user_a, db_session, login_as):
    """自分宛の通知のみ、新着順（created_at降順）で返ること。"""
    group, document = _make_group_and_document(db_session, user_a)

    n1 = AppNotification(
        group_id=group.id,
        triggered_by=user_a.id,
        user_id=user_a.id,
        document_id=document.id,
        message="1件目の通知",
    )
    n2 = AppNotification(
        group_id=group.id,
        triggered_by=user_a.id,
        user_id=user_a.id,
        document_id=document.id,
        message="2件目の通知",
    )
    db_session.add(n1)
    db_session.add(n2)
    db_session.commit()

    with login_as(user_a):
        res = client.get("/v1/notifications")

    assert res.status_code == 200
    messages = [n["message"] for n in res.json()]
    # 新着順なので、後から作ったn2が先に来るはず
    assert messages.index("2件目の通知") < messages.index("1件目の通知")

    _cleanup(db_session, group, document, [n1.id, n2.id])


def test_mark_notification_as_read_success(user_a, db_session, login_as):
    """自分宛の通知を既読にできること。"""
    group, document = _make_group_and_document(db_session, user_a)

    notification = AppNotification(
        group_id=group.id,
        triggered_by=user_a.id,
        user_id=user_a.id,
        document_id=document.id,
        message="既読化テスト用の通知",
        is_read=False,
    )
    db_session.add(notification)
    db_session.commit()

    with login_as(user_a):
        res = client.patch(f"/v1/notifications/{notification.id}/read")

    assert res.status_code == 200
    assert res.json()["is_read"] is True

    _cleanup(db_session, group, document, [notification.id])


def test_mark_notification_as_read_not_owned_returns_404(
    user_a, user_b, db_session, login_as
):
    """他人宛の通知を既読にしようとすると404になること。"""
    group, document = _make_group_and_document(db_session, user_a)

    notification = AppNotification(
        group_id=group.id,
        triggered_by=user_a.id,
        user_id=user_a.id,  # user_a宛の通知
        document_id=document.id,
        message="他人宛通知テスト",
    )
    db_session.add(notification)
    db_session.commit()

    # user_bが、自分宛ではないuser_aの通知を既読にしようとする
    with login_as(user_b):
        res = client.patch(f"/v1/notifications/{notification.id}/read")

    assert res.status_code == 404

    _cleanup(db_session, group, document, [notification.id])