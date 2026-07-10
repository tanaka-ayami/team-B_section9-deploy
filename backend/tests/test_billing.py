"""
課金API（POST /v1/billing/checkout-session）のテスト。
docker compose exec backend pytest tests/test_billing.py -v で実行確認用。

方針：
- Stripe本体との通信（stripe.checkout.Session.create）は実際に発生させず、
  unittest.mock.patchで差し替える。
- StripeErrorはコンストラクタにuser_messageを渡せないため、
  テストでは属性を後付けする形でモックする。
"""
from unittest.mock import MagicMock, patch

import stripe
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_checkout_session_success(user_a, db_session, login_as):
    """freeプランのユーザーがcheckout-sessionを作成できること。"""
    user_a.plan_status = "free"
    db_session.commit()

    fake_session = MagicMock()
    fake_session.url = "https://checkout.stripe.com/pay/dummy-session-id"

    with login_as(user_a):
        with patch(
            "app.api.v1.billing.stripe.checkout.Session.create",
            return_value=fake_session,
        ):
            res = client.post("/v1/billing/checkout-session")

    assert res.status_code == 201
    assert res.json()["checkout_url"] == "https://checkout.stripe.com/pay/dummy-session-id"


def test_create_checkout_session_already_premium(user_a, db_session, login_as):
    """既にpremiumのユーザーが呼ぶと409 ALREADY_PREMIUMになること。"""
    user_a.plan_status = "premium"
    db_session.commit()

    with login_as(user_a):
        res = client.post("/v1/billing/checkout-session")

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ALREADY_PREMIUM"

    # cleanup
    user_a.plan_status = "free"
    db_session.commit()


def test_create_checkout_session_stripe_error(user_a, db_session, login_as):
    """Stripe API側でエラーが起きた場合502 STRIPE_API_FAILEDになること。"""
    user_a.plan_status = "free"
    db_session.commit()

    stripe_error = stripe.error.StripeError("dummy stripe error")

    with login_as(user_a):
        with patch(
            "app.api.v1.billing.stripe.checkout.Session.create",
            side_effect=stripe_error,
        ):
            res = client.post("/v1/billing/checkout-session")

    assert res.status_code == 502
    assert res.json()["error"]["code"] == "STRIPE_API_FAILED"