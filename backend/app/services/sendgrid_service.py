"""
招待メール送信（SendGrid）。
issue #16時点ではSendGrid連携がまだ存在しないため、ログ出力のみのスタブとする。
SendGrid実装が入ったら、この関数の中身を実際のAPI呼び出しに差し替える。
"""
import logging

logger = logging.getLogger(__name__)

FRONTEND_BASE_URL = "http://localhost:3000"  # 本番ではVercelのドメインに変更


def send_invitation_email(to_email: str, group_name: str, token: str) -> None:
    invite_url = f"{FRONTEND_BASE_URL}/invitations/{token}"
    logger.info(
        "[STUB] 招待メール送信: to=%s group=%s url=%s", to_email, group_name, invite_url
    )