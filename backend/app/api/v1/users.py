"""
GET /v1/users/me
DBに登録済みのユーザー情報を返す。
未登録（signup前）の場合は404（get_current_userが返す）。

PATCH /v1/users/me
表示名（display_name）を更新する（issue #55）。
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps_db import get_current_user
from app.db.base import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserUpdate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=50)


def _user_to_dict(user: User) -> dict:
    """Userモデルをレスポンス用の辞書に変換する（共通処理）。"""
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "plan_status": user.plan_status,
        "monthly_scan_count": user.monthly_scan_count,
        "remind_days_before": user.remind_days_before,
    }


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return _user_to_dict(current_user)


@router.patch("/me")
def update_current_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    表示名（display_name）を更新する。
    プロフィール編集画面（issue #52）から呼ばれる。
    """
    current_user.display_name = payload.display_name
    db.commit()

    return _user_to_dict(current_user)