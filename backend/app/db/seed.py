"""
共通カテゴリの起動時シーディング。
group_id=NULLのカテゴリとして、アプリ起動時に存在しなければ追加する（idempotent）。
既存行にiconが未設定の場合は補完する（issue #16クローズ後にicon追加・11種に拡張）。
共通カテゴリはAPIから追加・編集・削除できない仕様のため、ここが唯一の管理場所になる。
"""
from sqlalchemy.orm import Session

from app.models import Category

# 「その他」は必ず最後（キャッチオール）に残す
DEFAULT_CATEGORIES = [
    {"name": "学校", "icon": "🎓"},
    {"name": "医療", "icon": "🏥"},
    {"name": "行政", "icon": "🏛️"},
    {"name": "保険", "icon": "🛡️"},
    {"name": "税金", "icon": "🧾"},
    {"name": "住居・暮らし", "icon": "🏠"},
    {"name": "子育て", "icon": "👶"},
    {"name": "介護", "icon": "🧑‍🦽"},
    {"name": "仕事", "icon": "💼"},
    {"name": "趣味", "icon": "🎨"},
    {"name": "その他", "icon": "📄"},
]


def seed_default_categories(db: Session) -> None:
    existing = {
        c.name: c for c in db.query(Category).filter(Category.group_id.is_(None)).all()
    }
    for item in DEFAULT_CATEGORIES:
        if item["name"] not in existing:
            db.add(Category(name=item["name"], group_id=None, icon=item["icon"]))
        else:
            category = existing[item["name"]]
            if category.icon is None:
                category.icon = item["icon"]
    db.commit()