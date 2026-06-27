"""
GET /v1/users/me

DBに登録済みのユーザー情報を返す。
未登録（signup前）の場合は404（get_current_userが返す）。
"""
from fastapi import APIRouter, Depends

from app.api.v1.deps_db import get_current_user
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "display_name": current_user.display_name,
        "plan_status": current_user.plan_status,
        "monthly_scan_count": current_user.monthly_scan_count,
        "remind_days_before": current_user.remind_days_before,
    }
