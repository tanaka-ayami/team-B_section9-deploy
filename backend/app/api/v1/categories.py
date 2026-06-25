"""
カテゴリAPI（issue #16）
- 追加・編集・削除はすべて「そのグループの管理者（Group.created_by）」のみ可能。
- 共通カテゴリ（group_id=NULL）の編集・削除も、どのグループの管理者として操作するかを
  クエリパラメータ ?group_id=xxx で明示してもらい、そのグループ内の管理者かどうかで判定する
  （「いずれかのグループの管理者であれば良い」という以前の方針から変更／チーム確認済み）。
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.errors import APIError
from app.db.base import get_db
from app.models.notification import Category
from app.models.user import Group, GroupMember, User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


def _user_group_ids(db: Session, user_id: uuid.UUID) -> list[uuid.UUID]:
    rows = db.query(GroupMember.group_id).filter(GroupMember.user_id == user_id).all()
    return [r[0] for r in rows]


def _get_category_or_404(db: Session, category_id: uuid.UUID) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "カテゴリが見つかりません")
    return category


def _is_group_admin(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """指定したグループの作成者（管理者）かどうか。"""
    return (
        db.query(Group)
        .filter(Group.id == group_id, Group.created_by == user_id)
        .first()
        is not None
    )


def _require_group_admin(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "グループが見つかりません")
    if group.created_by != user_id:
        raise APIError(403, "FORBIDDEN_GROUP_ACTION", "このグループの管理者のみ操作できます")


@router.get("", response_model=list[CategoryRead])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group_ids = _user_group_ids(db, current_user.id)
    return (
        db.query(Category)
        .filter(or_(Category.group_id.is_(None), Category.group_id.in_(group_ids)))
        .all()
    )


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # カテゴリ追加もグループの管理者のみ（以前の「メンバーなら誰でも追加可」から変更）
    _require_group_admin(db, body.group_id, current_user.id)

    category = Category(group_id=body.group_id, name=body.name, color_code=body.color_code)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: uuid.UUID,
    group_id: uuid.UUID,
    body: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    group_id：どのグループの管理者として操作するかを明示するクエリパラメータ。
    例）PATCH /v1/categories/{category_id}?group_id={group_id}
    """
    category = _get_category_or_404(db, category_id)

    # グループ専用カテゴリの場合、渡されたgroup_idがそのカテゴリの所属グループと
    # 一致しているか確認（他グループの管理者が無関係なカテゴリを操作できないようにする）
    if category.group_id is not None and category.group_id != group_id:
        raise APIError(403, "FORBIDDEN_GROUP_ACTION", "このカテゴリは指定されたグループに属していません")

    _require_group_admin(db, group_id, current_user.id)

    if body.name is not None:
        category.name = body.name
    if body.color_code is not None:
        category.color_code = body.color_code
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    group_id：どのグループの管理者として操作するかを明示するクエリパラメータ。
    例）DELETE /v1/categories/{category_id}?group_id={group_id}
    """
    category = _get_category_or_404(db, category_id)

    if category.group_id is not None and category.group_id != group_id:
        raise APIError(403, "FORBIDDEN_GROUP_ACTION", "このカテゴリは指定されたグループに属していません")

    _require_group_admin(db, group_id, current_user.id)

    db.delete(category)
    db.commit()