"""
groups.py の未カバー部分（グループ名変更・招待発行・招待一覧）のテスト。
docker compose exec backend pytest tests/test_groups_extra.py -v で実行確認用。

既存のtest_groups.pyとは別ファイルにして、既存ファイルへの影響を避ける。
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.invitation import Invitation
from app.models.user import Group, GroupMember

client = TestClient(app)


def test_update_group_name(user_a, db_session, login_as):
    """グループメンバーがグループ名を変更できること（issue #106対応）。"""
    group = Group(name="変更前のグループ名", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    with login_as(user_a):
        res = client.patch(f"/v1/groups/{group.id}", json={"name": "変更後のグループ名"})

    assert res.status_code == 200
    assert res.json()["name"] == "変更後のグループ名"

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_invite_to_group_creates_invitation_and_sends_email(
    user_a, db_session, login_as
):
    """招待発行時、invitationsレコードが作られ、SendGridの送信関数が呼ばれること。"""
    group = Group(name="招待テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    with login_as(user_a):
        with patch(
            "app.api.v1.groups.send_invitation_email", return_value=True
        ) as mock_send:
            res = client.post(
                f"/v1/groups/{group.id}/invite",
                json={"invitee_email": "invitee@example.com"},
            )

    assert res.status_code == 201
    body = res.json()
    assert body["invitee_email"] == "invitee@example.com"
    assert body["status"] == "pending"

    mock_send.assert_called_once()
    _, kwargs = mock_send.call_args
    assert kwargs["to_email"] == "invitee@example.com"
    assert kwargs["group_name"] == "招待テスト用グループ"

    invitation_id = body["id"]
    invitation = (
        db_session.query(Invitation).filter(Invitation.id == invitation_id).first()
    )
    assert invitation is not None
    assert invitation.token  # 空でないトークンが発行されていること

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation_id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_list_group_invitations_returns_only_pending(user_a, db_session, login_as):
    """招待一覧は、statusがpendingのものだけを返すこと。"""
    group = Group(name="招待一覧テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))

    from datetime import datetime, timedelta
    import secrets

    pending_invitation = Invitation(
        group_id=group.id,
        invited_by=user_a.id,
        invitee_email="pending@example.com",
        status="pending",
        token=secrets.token_urlsafe(16),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    accepted_invitation = Invitation(
        group_id=group.id,
        invited_by=user_a.id,
        invitee_email="accepted@example.com",
        status="accepted",
        token=secrets.token_urlsafe(16),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db_session.add(pending_invitation)
    db_session.add(accepted_invitation)
    db_session.commit()

    with login_as(user_a):
        res = client.get(f"/v1/groups/{group.id}/invitations")

    assert res.status_code == 200
    emails = [inv["invitee_email"] for inv in res.json()]
    assert "pending@example.com" in emails
    assert "accepted@example.com" not in emails

    # cleanup
    db_session.query(Invitation).filter(
        Invitation.id.in_([pending_invitation.id, accepted_invitation.id])
    ).delete(synchronize_session=False)
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()