"""
sendgrid_service.py のユニットテスト（APIエンドポイントを経由せず、
関数を直接呼び出して検証する）。
docker compose exec backend pytest tests/test_sendgrid_service.py -v で実行確認用。
"""
from unittest.mock import MagicMock, patch

from app.services import sendgrid_service


def test_send_email_success():
    """SendGrid送信が成功した場合、Trueが返ること。"""
    fake_response = MagicMock()
    fake_response.status_code = 202

    with patch.object(
        sendgrid_service, "SendGridAPIClient"
    ) as mock_client_cls:
        mock_client_cls.return_value.send.return_value = fake_response
        result = sendgrid_service._send_email(
            "to@example.com", "件名", "本文"
        )

    assert result is True


def test_send_email_failure_returns_false():
    """SendGrid送信で例外が起きた場合、Falseが返ること（呼び出し元は例外を意識しなくてよい）。"""
    with patch.object(
        sendgrid_service, "SendGridAPIClient"
    ) as mock_client_cls:
        mock_client_cls.return_value.send.side_effect = Exception("dummy send error")
        result = sendgrid_service._send_email(
            "to@example.com", "件名", "本文"
        )

    assert result is False


def test_send_reminder_email_builds_expected_content():
    """リマインドメールが、期限日・書類タイトルを含む内容で送信されること。"""
    with patch.object(sendgrid_service, "_send_email", return_value=True) as mock_send:
        result = sendgrid_service.send_reminder_email(
            "to@example.com", "夏期講習申込書", "2026-07-01"
        )

    assert result is True
    mock_send.assert_called_once()
    args, _ = mock_send.call_args
    to_email, subject, content = args
    assert to_email == "to@example.com"
    assert "夏期講習申込書" in subject
    assert "夏期講習申込書" in content
    assert "2026-07-01" in content