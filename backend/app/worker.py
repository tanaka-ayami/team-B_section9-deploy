from celery import Celery
from celery.schedules import crontab
import os

celery = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery.conf.timezone = "Asia/Tokyo"
celery.conf.enable_utc = False

# リマインドチェックを1分ごとに実行するスケジュール設定（Celery Beat用）
celery.conf.beat_schedule = {
    "check-reminders-every-minute": {
        "task": "app.worker.send_due_reminders",
        "schedule": 60.0,  # 60秒ごと
    },
    "reset-monthly-scan-count": {
        "task": "app.worker.reset_monthly_scan_count",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),
    },
}


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,   # 指数バックオフ（30秒→60秒→120秒…と間隔が伸びる）
    max_retries=3,
    retry_jitter=False,
)
def send_due_reminders(self):
    """
    notification_schedules を確認し、送信時刻になった予約のリマインドメールを送る。
    Celery Beat により定期的に実行される。
    """
    from datetime import datetime
    from app.db.base import SessionLocal
    from app.models.notification import NotificationSchedule
    from app.models.document import Document
    from app.models.user import User
    from app.services.sendgrid_service import send_reminder_email

    db = SessionLocal()
    try:
        due_schedules = (
            db.query(NotificationSchedule)
            .filter(
                NotificationSchedule.status == "pending",
                NotificationSchedule.scheduled_for <= datetime.utcnow(),
            )
            .all()
        )

        for schedule in due_schedules:
            user = db.query(User).filter(User.id == schedule.user_id).first()
            document = (
                db.query(Document).filter(Document.id == schedule.document_id).first()
            )

            if user is None or document is None:
                # 対象データが既に削除されている場合は送信せずキャンセル扱いにする
                schedule.status = "cancelled"
                db.commit()
                continue

            deadline_str = (
                document.deadline_date.isoformat() if document.deadline_date else "未設定"
            )

            success = send_reminder_email(
                to_email=user.email,
                document_title=document.title or "（無題の書類）",
                deadline_date=deadline_str,
            )

            if success:
                schedule.status = "sent"
            else:
                schedule.retry_count += 1
                if schedule.retry_count >= 3:
                    schedule.status = "failed"
                # 3回未満ならstatusはpendingのまま → 次回のBeat実行時に再試行される

            db.commit()

    finally:
        db.close()


@celery.task(bind=True, max_retries=3, retry_backoff=True)
def reset_monthly_scan_count(self):
    """
    毎月1日 AM0:00（JST）に、全ユーザーのmonthly_scan_countを0にリセットする。
    """
    from app.db.base import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        updated_count = db.query(User).update({"monthly_scan_count": 0})
        db.commit()
        return f"{updated_count}人分のスキャン枚数をリセットしました"
    finally:
        db.close()