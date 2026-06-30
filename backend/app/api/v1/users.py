"""
GET /v1/users/me
DBに登録済みのユーザー情報を返す。
未登録（signup前）の場合は404（get_current_userが返す）。

PATCH /v1/users/me
表示名（display_name）を更新する（issue #55）。
メール通知のON/OFF（email_notify_enabled）を更新する（issue #73）。
display_name・email_notify_enabledはそれぞれ任意項目とし、
リクエストで送られたフィールドのみを更新する（部分更新）。
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps_db import get_current_user
from app.db.base import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=50)
    email_notify_enabled: bool | None = None  # 【issue #73追加】未指定の場合は更新しない


def _user_to_dict(user: User) -> dict:
    """Userモデルをレスポンス用の辞書に変換する（共通処理）。"""
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "plan_status": user.plan_status,
        "monthly_scan_count": user.monthly_scan_count,
        "remind_days_before": user.remind_days_before,
        "email_notify_enabled": user.email_notify_enabled,  # 【issue #73追加】
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
    表示名（display_name）・メール通知設定（email_notify_enabled）を更新する。
    プロフィール編集画面（issue #52）・設定画面のリマインド設定（issue #73）から呼ばれる。
    どちらも任意項目のため、リクエストで送られたフィールドのみ更新する。
    """
    update_data = payload.model_dump(exclude_unset=True)

    if "display_name" in update_data:
        current_user.display_name = update_data["display_name"]

    if "email_notify_enabled" in update_data:
        current_user.email_notify_enabled = update_data["email_notify_enabled"]

    db.commit()

    return _user_to_dict(current_user)