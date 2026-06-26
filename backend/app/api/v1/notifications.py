from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
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

    ※ users.py のTODO（Alembic完了後にupsertする処理）が実装されたら、
      ここで自動作成するロジックに差し替える可能性あり（BE①と要相談）。
    """
    user = db.query(User).filter(User.firebase_uid == firebase_user["uid"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="ユーザー情報が見つかりません")
    return user


@router.get("/v1/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    """
    ログイン中のユーザー宛のお知らせ一覧を、新着順（created_at降順）で返す。
    """
    notifications = (
        db.query(AppNotification)
        .filter(AppNotification.user_id == current_user.id)
        .order_by(AppNotification.created_at.desc())
        .all()
    )

    return {
        "notifications": [
            {
                "id": str(n.id),
                "document_id": str(n.document_id),
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }


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
    