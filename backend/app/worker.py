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
    あわせて、グループの全メンバーに期限前のベルマーク通知（app_notifications）を作成する。
    Celery Beat により定期的に実行される。

    status の取りうる値：
      - pending   : 未送信（待機中）
      - sent      : 送信成功
      - failed    : 送信を試みたが3回失敗した
      - cancelled : 済スタンプ・書類削除等によりユーザー操作でキャンセルされた
      - skipped   : 【issue #73追加】ユーザーがメール通知をOFFにしているため、
                    意図的に送信しなかった（sent/failedとは区別する）

    ベルマーク通知（app_notifications）について：
      - メール通知の送受信結果（sent/skipped）に関わらず、全メンバーに通知を作成する
        （アプリ内通知は email_notify_enabled の設定に関わらず常時ON）
      - triggered_by には書類の登録者（document.created_by）を使用する
        （システム自動発生の通知のため、操作ユーザーは存在しない）
      - 重複防止：notification_schedules の status が pending から変わるタイミングで
        1回だけ作成するため、同じ書類について複数回通知が発生しない
    """
    from datetime import datetime
    from app.db.base import SessionLocal
    from app.models.notification import AppNotification, NotificationSchedule
    from app.models.document import Document
    from app.models.user import GroupMember, User
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

            # 【issue #73追加】メール通知をOFFにしているユーザーには送信しない。
            # アプリ内お知らせとは独立した設定であり、こちらはメールリマインドのみが対象。
            if not user.email_notify_enabled:
                schedule.status = "skipped"
            else:
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

            # 【issue #XX追加】期限前ベルマーク通知を全グループメンバーに作成する。
            # メール送信の成否・email_notify_enabledの設定に関わらず全員に届ける。
            # statusがpendingから変わるタイミングで作成するが、グループメンバー数分の
            # notification_schedulesが存在する場合、各スケジュール処理のたびに全員分を
            # 作成すると重複が発生するため、作成前に存在確認を行う（冪等性の担保）。
            if schedule.status != "pending":
                title = document.title or "（無題の書類）"
                message = f"「{title}」の期限が近づいています"

                group_members = (
                    db.query(GroupMember)
                    .filter(GroupMember.group_id == document.group_id)
                    .all()
                )

                for member in group_members:
                    already_exists = (
                        db.query(AppNotification)
                        .filter(
                            AppNotification.document_id == document.id,
                            AppNotification.user_id == member.user_id,
                            AppNotification.message == message,
                        )
                        .first()
                    )
                    if already_exists:
                        continue

                    notification = AppNotification(
                        group_id=document.group_id,
                        triggered_by=document.created_by,
                        user_id=member.user_id,
                        document_id=document.id,
                        message=message,
                    )
                    db.add(notification)

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