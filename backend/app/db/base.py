"""
DBのengine/sessionの定義。
テーブルがまだ存在しなくてもimportエラーにはならないので、
Alembic初期化前から書いておいて問題ない。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """全モデルの親クラス。Alembicの env.py から
    `from app.db.base import Base` して target_metadata = Base.metadata とする想定。
    """


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
