"""
docker compose exec backend pytest で実行確認用。
本物のFirebaseトークンが無くても、依存関数をオーバーライドして検証する。

get_current_user（DB取得込み）をオーバーライドすることで、
実際のDBに依存せずにレスポンスの形を検証する。
"""
from fastapi.testclient import TestClient

from app.api.v1.deps import get_current_firebase_user
from app.api.v1.deps_db import get_current_user
from app.main import app

client = TestClient(app)


class _FakeUser:
    id = "11111111-1111-1111-1111-111111111111"
    email = "test@example.com"
    display_name = "テスト太郎"
    plan_status = "free"
    monthly_scan_count = 0
    remind_days_before = 3
    


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_users_me_without_token_is_401():
    res = client.get("/v1/users/me")
    assert res.status_code == 401


def test_users_me_with_mocked_user():
    app.dependency_overrides[get_current_user] = lambda: _FakeUser()
    res = client.get("/v1/users/me")
    assert res.status_code == 200
    assert res.json()["display_name"] == "テスト太郎"
    app.dependency_overrides.clear()
