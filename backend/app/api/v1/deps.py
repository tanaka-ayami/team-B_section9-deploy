"""
リクエストヘッダーの Authorization: Bearer <idToken> を検証する依存関数。
DBには一切依存しないので、Alembic未着手でもこのまま動作確認できる。

フロントエンドはFirebase Auth SDKでログイン後に取得したIDトークンを
Authorization: Bearer <idToken> として送ってくる想定。
"""
from typing import TypedDict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from app.core.firebase import init_firebase

bearer_scheme = HTTPBearer(auto_error=False)


class FirebaseUser(TypedDict):
    uid: str
    email: str | None
    email_verified: bool


def get_current_firebase_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> FirebaseUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorizationヘッダーがありません",
        )

    init_firebase()

    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンの有効期限が切れています",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンが無効です",
        )

    return FirebaseUser(
        uid=decoded["uid"],
        email=decoded.get("email"),
        email_verified=decoded.get("email_verified", False),
    )
