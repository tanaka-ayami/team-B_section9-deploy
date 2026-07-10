"""
POST /v1/auth/signup のテスト。

このエンドポイントはget_current_user（conftest.pyのlogin_asがオーバーライドする対象）
ではなく、get_current_firebase_userに直接依存しているため、login_asは使えない。
ここでは get_current_firebase_user 自体を直接オーバーライドする。

docker compose exec backend pytest tests/test_auth.py -v で実行確認用。
"""
from fastapi.testclient import TestClient

from app.api.v1.deps import FirebaseUser, get_current_firebase_user
from app.main import app
from app.models.user import Group, GroupMember, User

client = TestClient(app)


def _override_firebase_user(uid: str, email: str):
    def _fake():
        return FirebaseUser(uid=uid, email=email, email_verified=True)

    app.dependency_overrides[get_current_firebase_user] = _fake


def _clear_override():
    app.dependency_overrides.pop(get_current_firebase_user, None)


def test_signup_creates_user_and_personal_group(db_session):
    """新規ユーザーの場合、user・個人グループ・group_membersが作られること。"""
    uid = "test-uid-signup-new"
    email = "signup-new@example.com"

    # 前提として、このuidのユーザーが存在しないことを確認
    db_session.query(User).filter(User.firebase_uid == uid).delete()
    db_session.commit()

    _override_firebase_user(uid, email)
    try:
        res = client.post("/v1/auth/signup", json={"display_name": "サインアップ太郎"})
    finally:
        _clear_override()

    assert res.status_code == 201
    body = res.json()
    assert body["user"]["display_name"] == "サインアップ太郎"
    assert body["personal_group"]["name"] == "サインアップ太郎"

    user = db_session.query(User).filter(User.firebase_uid == uid).first()
    assert user is not None

    group = db_session.query(Group).filter(Group.created_by == user.id).first()
    assert group is not None
    assert group.name == "サインアップ太郎"

    membership = (
        db_session.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == user.id)
        .first()
    )
    assert membership is not None

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.query(User).filter(User.id == user.id).delete()
    db_session.commit()


def test_signup_is_idempotent_for_existing_user(db_session):
    """既に登録済みのfirebase_uidの場合、新規作成せず既存データを返すこと。"""
    uid = "test-uid-signup-existing"
    email = "signup-existing@example.com"

    user = User(firebase_uid=uid, email=email, display_name="既存ユーザー")
    db_session.add(user)
    db_session.flush()
    group = Group(name="既存ユーザーの個人グループ", created_by=user.id)
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupMember(group_id=group.id, user_id=user.id))
    db_session.commit()

    _override_firebase_user(uid, email)
    try:
        res = client.post(
            "/v1/auth/signup", json={"display_name": "無視されるはずの名前"}
        )
    finally:
        _clear_override()

    assert res.status_code == 201
    body = res.json()
    # 既存のdisplay_nameがそのまま返り、リクエストのdisplay_nameでは上書きされないこと
    assert body["user"]["display_name"] == "既存ユーザー"
    assert body["personal_group"]["name"] == "既存ユーザーの個人グループ"

    # 重複してユーザーが作られていないこと
    user_count = db_session.query(User).filter(User.firebase_uid == uid).count()
    assert user_count == 1

    # cleanup
    db_session.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
    db_session.query(Group).filter(Group.id == group.id).delete()
    db_session.query(User).filter(User.id == user.id).delete()
    db_session.commit()