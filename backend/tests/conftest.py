"""
グループ・カテゴリ・招待API用の共通テストフィクスチャ。
get_current_firebase_user ではなく get_current_user を直接オーバーライドし、
本物のテストユーザー（DB上のUser行）を使って動作確認する。
※実際のPostgres（docker compose環境のDB）に書き込むため、各テストはcleanupを必須とする。
"""
from contextlib import contextmanager

import pytest

from app.api.v1.deps import get_current_user
from app.db.base import SessionLocal
from app.main import app
from app.models.user import User


def _get_or_create_user(
    db, firebase_uid: str, email: str, display_name: str = "テストユーザー"
) -> User:
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user is None:
        user = User(firebase_uid=firebase_uid, email=email, display_name=display_name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def user_a(db_session):
    """グループ作成者（管理者）役のテストユーザー。"""
    return _get_or_create_user(db_session, "test-uid-admin", "admin@example.com", "管理者")


@pytest.fixture
def user_b(db_session):
    """管理者ではない側（招待される側・一般メンバー）のテストユーザー。"""
    return _get_or_create_user(db_session, "test-uid-member", "member@example.com")


@pytest.fixture
def login_as():
    """with login_as(user): ... の形で、その間だけ current_user をそのユーザーに固定する。"""

    @contextmanager
    def _login_as(user: User):
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            yield user
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    return _login_as