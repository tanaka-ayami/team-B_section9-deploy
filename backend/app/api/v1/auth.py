"""
POST /v1/auth/signup

API設計.md の仕様：
Firebase認証後に呼ばれ、users作成＋個人グループ自動生成を行う。

【現状】Alembicでusersテーブルが出来るまでの仮実装。
DBへの保存は行わず、Firebaseトークンの検証が通ることだけを確認する。
レスポンスの形は本来のAPI設計に合わせてあるので、FE側の実装はこのまま進められる。
"""
from fastapi import APIRouter, Depends

from app.api.v1.deps import FirebaseUser, get_current_firebase_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=201)
def signup(current_user: FirebaseUser = Depends(get_current_firebase_user)):
    # TODO(Alembic完了後):
    # 1. users テーブルに firebase_uid で存在確認、無ければINSERT
    # 2. 個人グループの扱いが決まったら、必要であればgroups/group_membersも作成
    return {
        "user": {
            "id": None,  # TODO: 実際のDB上のUUIDに置き換え
            "email": current_user["email"],
            "plan_status": "free",
            "monthly_scan_count": 0,
            "remind_days_before": 1,
        },
        "note": "現在は仮実装です。DB接続後に正式なレスポンスへ更新されます。",
    }