"""
get_current_firebase_user（トークン検証のみ）の後段で、
DBから実際のUserレコードを取得する依存関数。

signup前のユーザー（まだDBに存在しない）には404を返す。
→ /v1/auth/signup 以外のほとんどのエンドポイントはこちらを使う想定。
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import FirebaseUser, get_current_firebase_user
from app.db.base import get_db
from app.models import User


def get_current_user(
    firebase_user: FirebaseUser = Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.firebase_uid == firebase_user["uid"]).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが登録されていません。先にサインアップしてください。",
        )
    return user
