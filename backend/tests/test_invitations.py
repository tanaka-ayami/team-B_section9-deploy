"""
docker compose exec backend pytest app/tests/test_invitations.py -v で実行確認用。
SendGridはスタブ（ログ出力のみ）なので、トークンはAPIレスポンスではなくDBから直接取得する
（本番でも招待リンクはメール経由でしか手に入らないため、これは実際の使われ方に近い）。
"""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.invitation import Invitation
from app.models.user import Group, GroupMember

client = TestClient(app)


def test_invite_and_accept_flow(user_a, user_b, db_session, login_as):
    with login_as(user_a):
        group_res = client.post("/v1/groups", json={"name": "招待テスト用"})
        group_id = group_res.json()["id"]

        res = client.post(
            f"/v1/groups/{group_id}/invite",
            json={"invitee_email": user_b.email},
        )
        assert res.status_code == 201

    invitation = (
        db_session.query(Invitation)
        .filter(Invitation.group_id == group_id, Invitation.invitee_email == user_b.email)
        .order_by(Invitation.created_at.desc())
        .first()
    )
    assert invitation is not None
    token = invitation.token

    # 認証不要：招待ページ表示用
    res = client.get(f"/v1/invitations/{token}")
    assert res.status_code == 200
    assert res.json()["status"] == "pending"

    with login_as(user_b):
        res = client.post(f"/v1/invitations/{token}/accept")
        assert res.status_code == 200
        assert res.json()["status"] == "accepted"

        # 2回目は既に処理済みなので409
        res = client.post(f"/v1/invitations/{token}/accept")
        assert res.status_code == 409

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation.id).delete()
    db_session.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    db_session.query(Group).filter(Group.id == group_id).delete()
    db_session.commit()


def test_accept_expired_invitation_returns_410(user_a, user_b, db_session, login_as):
    with login_as(user_a):
        group_res = client.post("/v1/groups", json={"name": "期限切れテスト用"})
        group_id = group_res.json()["id"]

    invitation = Invitation(
        group_id=group_id,
        invited_by=user_a.id,
        invitee_email=user_b.email,
        token="expired-test-token-001",
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(invitation)
    db_session.commit()

    # GET単体は期限チェックをしない仕様（FE側で期限切れ表示を出す想定）なので200のまま
    res = client.get(f"/v1/invitations/{invitation.token}")
    assert res.status_code == 200

    with login_as(user_b):
        res = client.post(f"/v1/invitations/{invitation.token}/accept")
        assert res.status_code == 410
        assert res.json()["error"]["code"] == "INVITATION_EXPIRED"

    # cleanup
    db_session.query(Invitation).filter(Invitation.id == invitation.id).delete()
    db_session.query(Group).filter(Group.id == group_id).delete()
    db_session.commit()