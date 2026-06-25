"""
GET /users/me

Week1ゴール「ログイン→JWT取得→カレンダー画面遷移」の確認用。
今はDBにまだ書き込まず、Firebaseトークンの中身をそのまま返すだけ。
→ Alembicでusersテーブルができたら、ここで
   「DBにfirebase_uidが無ければ作成」というロジックを追加する。今はTODOコメントで明示しておく。
   （個人グループ自動生成は不要そうなので方針変更：チーム確認の上、削除または別実装に変更予定）
"""
from fastapi import APIRouter, Depends

from app.api.v1.deps import FirebaseUser, get_current_firebase_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_current_user(current_user: FirebaseUser = Depends(get_current_firebase_user)):
    # TODO(Alembic完了後): users テーブルに firebase_uid で upsert する。
    return {
        "firebase_uid": current_user["uid"],
        "email": current_user["email"],
        "email_verified": current_user["email_verified"],
    }