"""
共通カテゴリ（学校・医療・行政・保険・その他）の起動時シーディング。
group_id=NULLのカテゴリとして、アプリ起動時に存在しなければ追加する（idempotent）。
issue #12 MVP外チェックリスト対応。
"""
from sqlalchemy.orm import Session

from app.models import Category

DEFAULT_CATEGORY_NAMES = ["学校", "医療", "行政", "保険", "その他"]


def seed_default_categories(db: Session) -> None:
    """すでに同名の共通カテゴリ（group_id=NULL）があればスキップし、無ければ追加する。"""
    existing_names = {
        c.name for c in db.query(Category).filter(Category.group_id.is_(None)).all()
    }
    for name in DEFAULT_CATEGORY_NAMES:
        if name not in existing_names:
            db.add(Category(name=name, group_id=None))
    db.commit()