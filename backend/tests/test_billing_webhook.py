"""
POST /v1/billing/webhook のテスト。
docker compose exec backend pytest tests/test_billing_webhook.py -v で実行確認用。

stripe.Webhook.construct_eventをモック化し、実際のStripe署名検証は行わない。
"""
from unittest.mock import MagicMock, patch

import stripe
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_webhook_invalid_signature_returns_400():
    """署名検証に失敗した場合、400を返すこと。"""
    with patch(
        "app.api.v1.billing.stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError(
            "invalid signature", "sig_header"
        ),
    ):
        res = client.post(
            "/v1/billing/webhook",
            content=b"dummy payload",
            headers={"stripe-signature": "dummy-signature"},
        )

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_WEBHOOK_SIGNATURE"


def test_webhook_checkout_completed_updates_plan_status(user_a, db_session):
    """
    checkout.session.completedイベントを受信した場合、
    client_reference_idに対応するユーザーのplan_statusがpremiumになること。
    """
    user_a.plan_status = "free"
    db_session.commit()

    fake_session = MagicMock()
    fake_session.to_dict.return_value = {"client_reference_id": str(user_a.id)}

    fake_event = {
        "type": "checkout.session.completed",
        "data": {"object": fake_session},
    }

    with patch(
        "app.api.v1.billing.stripe.Webhook.construct_event",
        return_value=fake_event,
    ):
        res = client.post(
            "/v1/billing/webhook",
            content=b"dummy payload",
            headers={"stripe-signature": "dummy-signature"},
        )

    assert res.status_code == 200
    assert res.json() == {"received": True}

    db_session.commit()
    assert user_a.plan_status == "premium"

    # cleanup
    user_a.plan_status = "free"
    db_session.commit()


def test_webhook_unknown_user_id_still_returns_200(db_session):
    """
    client_reference_idに対応するユーザーが存在しない場合でも、
    Stripe側の再送を防ぐため200を返すこと。
    """
    fake_session = MagicMock()
    fake_session.to_dict.return_value = {
        "client_reference_id": "00000000-0000-0000-0000-000000000000"
    }

    fake_event = {
        "type": "checkout.session.completed",
        "data": {"object": fake_session},
    }

    with patch(
        "app.api.v1.billing.stripe.Webhook.construct_event",
        return_value=fake_event,
    ):
        res = client.post(
            "/v1/billing/webhook",
            content=b"dummy payload",
            headers={"stripe-signature": "dummy-signature"},
        )

    assert res.status_code == 200
    assert res.json() == {"received": True}


def test_webhook_unhandled_event_type_still_returns_200():
    """未対応のイベント種別でも200を返すこと（Stripeの再送防止）。"""
    fake_event = {"type": "some.other.event", "data": {"object": MagicMock()}}

    with patch(
        "app.api.v1.billing.stripe.Webhook.construct_event",
        return_value=fake_event,
    ):
        res = client.post(
            "/v1/billing/webhook",
            content=b"dummy payload",
            headers={"stripe-signature": "dummy-signature"},
        )

    assert res.status_code == 200
    assert res.json() == {"received": True}