"""
docker compose exec backend pytest app/tests/test_groups.py -v で実行確認用。
"""
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import Group, GroupMember

client = TestClient(app)


def test_create_and_list_groups(user_a, db_session, login_as):
    with login_as(user_a):
        res = client.post("/v1/groups", json={"name": "テストグループ"})
        assert res.status_code == 201
        group = res.json()
        assert group["created_by"] == str(user_a.id)

        res = client.get("/v1/groups")
        assert res.status_code == 200
        assert any(g["id"] == group["id"] for g in res.json())

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group["id"]).delete()
    db_session.query(Group).filter(Group.id == group["id"]).delete()
    db_session.commit()


def test_delete_group_forbidden_for_non_creator(user_a, user_b, db_session, login_as):
    with login_as(user_a):
        res = client.post("/v1/groups", json={"name": "削除テスト用"})
        group_id = res.json()["id"]

    with login_as(user_b):
        # user_bは作成者ではないので403
        res = client.delete(f"/v1/groups/{group_id}")
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "FORBIDDEN_GROUP_ACTION"

    with login_as(user_a):
        # user_aは作成者なので204で削除できる
        res = client.delete(f"/v1/groups/{group_id}")
        assert res.status_code == 204

    # cleanup（group_membersはON DELETE CASCADEなので自動で消えているはず）
    db_session.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    db_session.query(Group).filter(Group.id == group_id).delete()
    db_session.commit()