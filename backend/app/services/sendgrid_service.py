"""
SendGridを使ったメール送信処理。

招待メール（issue #16）とリマインドメール（issue #21）の両方を扱う。
"""
import logging
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

FRONTEND_BASE_URL = "http://localhost:3000"  # 本番ではVercelのドメインに変更

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")


def _send_email(to_email: str, subject: str, content: str) -> bool:
    """
    SendGrid経由でメールを送信する共通処理。

    Returns:
        bool: 送信成功時はTrue、失敗時はFalse
    """
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(
            "メール送信成功: to=%s subject=%s status=%s",
            to_email, subject, response.status_code,
        )
        return True
    except Exception as e:
        logger.error("メール送信失敗: to=%s subject=%s error=%s", to_email, subject, e)
        return False


def send_invitation_email(to_email: str, group_name: str, token: str) -> bool:
    """
    グループ招待メールを送信する（issue #16）。
    """
    invite_url = f"{FRONTEND_BASE_URL}/invitations/{token}"
    subject = f"「{group_name}」グループへの招待"
    content = (
        f"あなたは「{group_name}」グループに招待されました。\n\n"
        f"以下のリンクから参加してください。\n{invite_url}"
    )
    return _send_email(to_email, subject, content)


def send_reminder_email(to_email: str, document_title: str, deadline_date: str) -> bool:
    """
    書類の期限リマインドメールを送信する（issue #21）。
    """
    subject = f"【リマインド】「{document_title}」の期限が近づいています"
    content = (
        f"「{document_title}」の提出・対応期限が近づいています。\n\n"
        f"期限：{deadline_date}\n\n"
        f"アプリを開いて確認してください。"
    )
    return _send_email(to_email, subject, content)
    