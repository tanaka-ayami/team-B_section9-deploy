"""
docker compose exec backend pytest で実行確認用。
本物のFirebaseトークンが無くても、依存関数をオーバーライドして検証する。
"""
from fastapi.testclient import TestClient

from app.api.v1.deps import get_current_firebase_user
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_users_me_without_token_is_401():
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401


def test_users_me_with_mocked_token():
    app.dependency_overrides[get_current_firebase_user] = lambda: {
        "uid": "test-uid-123",
        "email": "test@example.com",
        "email_verified": True,
    }
    res = client.get("/api/v1/users/me")
    assert res.status_code == 200
    assert res.json()["firebase_uid"] == "test-uid-123"
    app.dependency_overrides.clear()
