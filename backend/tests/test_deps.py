"""
app/api/v1/deps.py のテスト（get_current_firebase_user・get_current_user）。

init_firebase()・firebase_auth.verify_id_tokenは実際には呼び出さず、
モック化して検証する。deps.pyのget_current_user関連テストは、既に
conftest.pyでオーバーライド済みの他テストとは独立して、この関数自体の
振る舞い（未登録ユーザーの自動作成=upsert）を直接確認する。

docker compose exec backend pytest tests/test_deps.py -v で実行確認用。
"""
from unittest.mock import patch

from fastapi.testclient import TestClient
from firebase_admin import auth as firebase_auth

from app.api.v1.deps import FirebaseUser, get_current_firebase_user, get_current_user
from app.db.base import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app)


def test_missing_authorization_header_returns_401():
    """Authorizationヘッダーが無い場合、401になること。"""
    # get_current_userに依存する既存のGETエンドポイントで確認
    res = client.get("/v1/users/me")
    assert res.status_code == 401


def test_get_current_firebase_user_expired_token_returns_401():
    """トークンの有効期限切れの場合、401になること。"""

    def _raise_expired(token):
        raise firebase_auth.ExpiredIdTokenError("expired", cause=None)

    with patch("app.api.v1.deps.init_firebase", return_value=None), patch(
        "app.api.v1.deps.firebase_auth.verify_id_token", side_effect=_raise_expired
    ):
        res = client.get(
            "/v1/users/me", headers={"Authorization": "Bearer dummy-expired-token"}
        )

    assert res.status_code == 401


def test_get_current_firebase_user_invalid_token_returns_401():
    """トークンが不正な場合、401になること。"""
    with patch("app.api.v1.deps.init_firebase", return_value=None), patch(
        "app.api.v1.deps.firebase_auth.verify_id_token",
        side_effect=Exception("invalid token"),
    ):
        res = client.get(
            "/v1/users/me", headers={"Authorization": "Bearer dummy-invalid-token"}
        )

    assert res.status_code == 401


def test_get_current_user_creates_user_if_not_exists(db_session):
    """
    app.api.v1.deps.get_current_user自体の挙動を直接検証する。
    注：この関数はどのエンドポイントからも実際には呼ばれておらず、
    使用されているのは同名だが別実装のapp.api.v1.deps_db.get_current_user
    （未登録なら404を返す版）である。deps.py側は現状デッドコードと判明したため、
    関数を直接呼び出して検証する。
    """
    uid = "test-uid-deps-auto-create"
    email = "deps-auto-create@example.com"

    db_session.query(User).filter(User.firebase_uid == uid).delete()
    db_session.commit()

    fake_firebase_user = FirebaseUser(uid=uid, email=email, email_verified=True)

    result = get_current_user(firebase_user=fake_firebase_user, db=db_session)

    assert result.firebase_uid == uid
    # display_nameはメールの@より前がフォールバックとして使われる
    assert result.display_name == "deps-auto-create"

    # cleanup
    db_session.query(User).filter(User.id == result.id).delete()
    db_session.commit()