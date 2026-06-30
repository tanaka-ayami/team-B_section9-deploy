"""
カテゴリAPI（issue #16クローズ後の最終方針）
カテゴリは固定11種類の共通カテゴリのみで運用する。
グループ独自カテゴリという概念は廃止したため、追加・編集・削除のAPIは提供しない。
一覧取得のみ。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps_db import get_current_user
from app.db.base import get_db
from app.models.notification import Category
from app.models.user import User
from app.schemas.category import CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """固定11種類の共通カテゴリを返す（group_id=NULLのもの全件）。"""
    return db.query(Category).filter(Category.group_id.is_(None)).all()