"""
groups.py の404/403異常系のテスト（_get_group_or_404・_require_member関連）。
docker compose exec backend pytest tests/test_groups_errors.py -v で実行確認用。
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.models.user import Group, GroupMember

client = TestClient(app)

NON_EXISTENT_GROUP_ID = uuid.uuid4()


def test_get_group_members_not_found_returns_404(user_a, login_as):
    """存在しないグループIDでメンバー一覧を取得しようとすると404になること。"""
    with login_as(user_a):
        res = client.get(f"/v1/groups/{NON_EXISTENT_GROUP_ID}/members")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_group_members_forbidden_for_non_member(user_a, user_b, db_session, login_as):
    """グループのメンバーでないユーザーがメンバー一覧を取得しようとすると403になること。"""
    group = Group(name="非メンバーテスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    with login_as(user_b):
        res = client.get(f"/v1/groups/{group.id}/members")

    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN_GROUP_ACTION"

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_update_group_not_found_returns_404(user_a, login_as):
    """存在しないグループを更新しようとすると404になること。"""
    with login_as(user_a):
        res = client.patch(
            f"/v1/groups/{NON_EXISTENT_GROUP_ID}", json={"name": "新しい名前"}
        )

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_update_group_forbidden_for_non_member(user_a, user_b, db_session, login_as):
    """グループのメンバーでないユーザーは名前を変更できず403になること。"""
    group = Group(name="更新権限テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    with login_as(user_b):
        res = client.patch(f"/v1/groups/{group.id}", json={"name": "勝手に変更"})

    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN_GROUP_ACTION"

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()


def test_invite_to_group_not_found_returns_404(user_a, login_as):
    """存在しないグループへ招待しようとすると404になること。"""
    with login_as(user_a):
        res = client.post(
            f"/v1/groups/{NON_EXISTENT_GROUP_ID}/invite",
            json={"invitee_email": "someone@example.com"},
        )

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_invite_to_group_forbidden_for_non_member(user_a, user_b, db_session, login_as):
    """グループのメンバーでないユーザーは招待を発行できず403になること。"""
    group = Group(name="招待権限テスト用グループ", created_by=user_a.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user_a.id))
    db_session.commit()

    with login_as(user_b):
        res = client.post(
            f"/v1/groups/{group.id}/invite",
            json={"invitee_email": "someone@example.com"},
        )

    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN_GROUP_ACTION"

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.commit()