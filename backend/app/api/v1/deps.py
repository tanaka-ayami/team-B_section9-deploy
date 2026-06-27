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
from sqlalchemy.orm import Session

from app.core.firebase import init_firebase
from app.db.base import get_db
from app.models.user import User

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


def get_current_user(
    firebase_user: FirebaseUser = Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Firebaseで検証済みのuidから、DB上のUser行を取得する（issue #16で追加）。
    未登録（初回ログイン）の場合はその場で作成する（upsert）。
    display_nameはNOT NULLのため、メールの@より前をフォールバックとして使用する。
    """
    user = db.query(User).filter(User.firebase_uid == firebase_user["uid"]).first()
    if user is None:
        email = firebase_user["email"] or ""
        user = User(
            firebase_uid=firebase_user["uid"],
            email=email,
            display_name=email.split("@")[0] if email else "ユーザー",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user