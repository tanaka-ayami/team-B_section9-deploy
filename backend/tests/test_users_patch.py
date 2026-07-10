"""
PATCH /v1/users/me のテスト（プロフィール・設定更新）。
docker compose exec backend pytest tests/test_users_patch.py -v で実行確認用。

既存のtest_users.pyはGET /v1/users/meのみ、かつ_FakeUser（DBに実体を持たない
仮のオブジェクト）でモックする独自スタイルだったため、実際のDB更新を検証したい
今回はconftest.py側のuser_a・login_asパターンを使う。
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_update_display_name_only(user_a, db_session, login_as):
    """display_nameのみ送った場合、他のフィールドは変わらないこと。"""
    user_a.display_name = "元の名前"
    user_a.remind_days_before = 3
    db_session.commit()

    with login_as(user_a):
        res = client.patch("/v1/users/me", json={"display_name": "更新後の名前"})

    assert res.status_code == 200
    body = res.json()
    assert body["display_name"] == "更新後の名前"
    assert body["remind_days_before"] == 3

    db_session.commit()
    assert user_a.display_name == "更新後の名前"

    # cleanup
    user_a.display_name = "元の名前"
    db_session.commit()


def test_update_remind_days_before_only(user_a, db_session, login_as):
    """remind_days_beforeのみ送った場合、正しく反映されること（issue #77）。"""
    user_a.remind_days_before = 3
    db_session.commit()

    with login_as(user_a):
        res = client.patch("/v1/users/me", json={"remind_days_before": 5})

    assert res.status_code == 200
    assert res.json()["remind_days_before"] == 5

    db_session.commit()
    assert user_a.remind_days_before == 5

    # cleanup
    user_a.remind_days_before = 3
    db_session.commit()


def test_update_multiple_fields_at_once(user_a, db_session, login_as):
    """複数フィールドを同時に更新できること。"""
    user_a.display_name = "元の名前"
    user_a.email_notify_enabled = True
    user_a.remind_days_before = 3
    db_session.commit()

    with login_as(user_a):
        res = client.patch(
            "/v1/users/me",
            json={
                "display_name": "まとめて更新",
                "email_notify_enabled": False,
                "remind_days_before": 7,
            },
        )

    assert res.status_code == 200
    body = res.json()
    assert body["display_name"] == "まとめて更新"
    assert body["email_notify_enabled"] is False
    assert body["remind_days_before"] == 7

    # cleanup
    user_a.display_name = "元の名前"
    user_a.email_notify_enabled = True
    user_a.remind_days_before = 3
    db_session.commit()