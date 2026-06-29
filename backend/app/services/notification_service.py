from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.notification import AppNotification, NotificationSchedule
from app.models.user import User
from app.services.group_service import get_group_member_user_ids


def create_document_notifications(
    db: Session, group_id, document_id, created_by_user_id
):
    """
    書類登録時に、登録者以外のグループメンバーへ通知レコードを作成する。
    メッセージには登録者の表示名（display_name）を使用する。
    """
    member_ids = get_group_member_user_ids(db, group_id)

    creator = db.query(User).filter(User.id == created_by_user_id).first()
    creator_name = creator.display_name if creator else "メンバー"

    for member_id in member_ids:
        if member_id == created_by_user_id:
            continue  # 登録者本人には通知しない

        notification = AppNotification(
            group_id=group_id,
            triggered_by=created_by_user_id,
            document_id=document_id,
            message=f"{creator_name}さんが書類を登録しました",
        )
        db.add(notification)


def create_reminder_schedules(db: Session, group_id, document_id, deadline_date):
    """
    期限がある書類が登録されたとき、グループメンバー全員分のリマインド予約を作成する。
    """
    member_ids = get_group_member_user_ids(db, group_id)

    users = db.query(User).filter(User.id.in_(member_ids)).all()

    for user in users:
        scheduled_for = deadline_date - timedelta(days=user.remind_days_before)

        schedule = NotificationSchedule(
            document_id=document_id,
            user_id=user.id,
            scheduled_for=scheduled_for,
            status="pending",
        )
        db.add(schedule)


def cancel_pending_reminders(db: Session, document_id):
    """
    指定した書類に紐づく、まだ送信していないリマインド予約（status='pending'）を
    すべて 'cancelled' に更新する。

    済スタンプON時・書類削除時に呼ばれる想定。
    """
    db.query(NotificationSchedule).filter(
        NotificationSchedule.document_id == document_id,
        NotificationSchedule.status == "pending",
    ).update({"status": "cancelled"})