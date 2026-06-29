from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.notification import AppNotification
from app.models.user import User
from app.api.v1.deps import FirebaseUser, get_current_firebase_user

router = APIRouter()


def get_current_db_user(
    firebase_user: FirebaseUser = Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
) -> User:
    """
    FirebaseのuidからDB上のUserレコードを取得する。
    まだusersテーブルにレコードが無い場合は404を返す。
    """
    user = db.query(User).filter(User.firebase_uid == firebase_user["uid"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="ユーザー情報が見つかりません")
    return user


class AppNotificationResponse(BaseModel):
    """
    FE側の型定義（AppNotification interface）に合わせたレスポンス用スキーマ。
    """
    id: str
    group_id: str
    triggered_by: str
    document_id: str
    message: str
    is_read: bool
    created_at: str


def _notification_to_dict(n: AppNotification) -> dict:
    """AppNotificationモデルをレスポンス用の辞書に変換する（共通処理）。"""
    return {
        "id": str(n.id),
        "group_id": str(n.group_id),
        "triggered_by": str(n.triggered_by),
        "document_id": str(n.document_id),
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
    }


@router.get("/v1/notifications", response_model=list[AppNotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    """
    ログイン中のユーザー宛のお知らせ一覧を、新着順（created_at降順）で返す。
    レスポンスは配列を直接返す（FE側の型定義 AppNotification[] に合わせる）。
    """
    notifications = (
        db.query(AppNotification)
        .filter(AppNotification.user_id == current_user.id)
        .order_by(AppNotification.created_at.desc())
        .all()
    )

    return [_notification_to_dict(n) for n in notifications]


@router.patch("/v1/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    """
    指定したお知らせを既読（is_read=True）に更新する。
    """
    notification = (
        db.query(AppNotification)
        .filter(
            AppNotification.id == notification_id,
            AppNotification.user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(status_code=404, detail="お知らせが見つかりません")

    notification.is_read = True
    db.commit()

    return {"id": str(notification.id), "is_read": notification.is_read}