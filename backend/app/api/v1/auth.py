"""
POST /v1/auth/signup

API設計.md の仕様：
Firebase認証後に呼ばれ、users作成＋個人グループ自動生成を行う。

【本実装】
1. firebase_uidでusersを検索。すでに存在すれば、新規作成せずそのまま返す
   （FE側が再ログイン時にもこのAPIを呼ぶ可能性があるため、安全のため冪等にしている）
2. 存在しなければ、以下を1トランザクションで作成する
   - users（display_nameはFEから受け取った必須項目）
   - groups（name=display_nameそのまま）
   - group_members（作成したuserと作成したgroupを紐付け）
"""
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.deps import FirebaseUser, get_current_firebase_user
from app.db.base import get_db
from app.models import Group, GroupMember, User

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=50)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    body: SignupRequest,
    current_user: FirebaseUser = Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
):
    # 既に登録済みなら新規作成せずそのまま返す（再ログイン時にこのAPIを叩いても安全にするため）
    existing = db.query(User).filter(User.firebase_uid == current_user["uid"]).first()
    if existing is not None:
        existing_group = (
            db.query(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .filter(GroupMember.user_id == existing.id)
            .first()
        )
        return _build_response(existing, existing_group)

    user = User(
        firebase_uid=current_user["uid"],
        email=current_user["email"],
        display_name=body.display_name,
    )
    db.add(user)
    db.flush()  # user.id を確定させる（コミット前にIDが必要なため）

    group = Group(
        name=body.display_name,
        created_by=user.id,
    )
    db.add(group)
    db.flush()  # group.id を確定させる

    membership = GroupMember(group_id=group.id, user_id=user.id)
    db.add(membership)

    db.commit()

    return _build_response(user, group)


def _build_response(user: User, group: Group | None = None):
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "plan_status": user.plan_status,
            "monthly_scan_count": user.monthly_scan_count,
            "remind_days_before": user.remind_days_before,
        },
        "personal_group": (
            {"id": str(group.id), "name": group.name} if group is not None else None
        ),
    }