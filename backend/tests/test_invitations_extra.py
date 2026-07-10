"""
招待受諾API（GET /v1/invitations/{token}、accept、reject）のテスト。
docker compose exec backend pytest tests/test_invitations_extra.py -v で実行確認用。

既存のtest_invitations.pyとは別ファイルにして、既存ファイルへの影響を避ける。
"""
import secrets
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.invitation import Invitation
from app.models.user import Group, GroupMember

client = TestClient(app)


def _make_invitation(db_session, group, invitee_email, status="pending", expires_in_days=7):
    invitation = Invitation(
        group_id=group.id,
        invited_by=group.created_by,
        invitee_email=invitee_email,
        status=status,
        token=secrets.token_urlsafe(16),
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
    )
    db_session.add(invitation)
    db_session.commit()
    return invitation


def test_get_invitation_not_found_returns_404(db_session):
    """存在しないトークンでは404が返ること。"""
    res = client.get("/v1/invitations/not-a-real-token")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_accept_invitation_success(user_a, user_b, db_session, login_as):
    """招待されたメールアドレスと一致するユーザーが承諾すると、
    group_membersに追加され、statusがacceptedになること。"""
    group = Group(name="招待受諾テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    invitation = _make_invitation(db_session, group, user_b.email)

    with login_as(user_b):
        res = client.post(f"/v1/invitations/{invitation.token}/accept")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["group_id"] == str(group.id)

    db_session.commit()
    assert invitation.status == "accepted"

    member = (
        db_session.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == user_b.id)
        .first()
    )
    assert member is not None

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_accept_invitation_email_mismatch_returns_403(user_a, user_b, db_session, login_as):
    """招待されたメールアドレスと違うユーザーが承諾しようとすると403になること。"""
    group = Group(name="メール不一致テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    # 招待先はuser_bのメールではなく、全く別のメールアドレス
    invitation = _make_invitation(db_session, group, "someone-else@example.com")

    with login_as(user_b):
        res = client.post(f"/v1/invitations/{invitation.token}/accept")

    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INVITATION_EMAIL_MISMATCH"

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_accept_invitation_expired_returns_410(user_a, user_b, db_session, login_as):
    """期限切れの招待を承諾しようとすると410になること。"""
    group = Group(name="期限切れテスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    invitation = _make_invitation(
        db_session, group, user_b.email, expires_in_days=-1
    )

    with login_as(user_b):
        res = client.post(f"/v1/invitations/{invitation.token}/accept")

    assert res.status_code == 410
    assert res.json()["error"]["code"] == "INVITATION_EXPIRED"

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_reject_invitation_success(user_a, user_b, db_session, login_as):
    """招待を拒否すると、statusがrejectedになること。"""
    group = Group(name="拒否テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    invitation = _make_invitation(db_session, group, user_b.email)

    with login_as(user_b):
        res = client.post(f"/v1/invitations/{invitation.token}/reject")

    assert res.status_code == 200
    assert res.json()["status"] == "rejected"

    db_session.commit()
    assert invitation.status == "rejected"

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_reject_already_handled_invitation_returns_409(
    user_a, user_b, db_session, login_as
):
    """既にaccepted/rejected済みの招待を再度拒否しようとすると409になること。"""
    group = Group(name="重複処理テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    invitation = _make_invitation(db_session, group, user_b.email, status="rejected")

    with login_as(user_b):
        res = client.post(f"/v1/invitations/{invitation.token}/reject")

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INVITATION_ALREADY_HANDLED"

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()