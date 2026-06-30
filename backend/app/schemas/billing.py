"""
課金（Stripe）関連のスキーマ（issue #22）。
"""
from pydantic import BaseModel


class CheckoutSessionRead(BaseModel):
    """
    POST /v1/billing/checkout-session のレスポンス。
    フロントエンドはこの checkout_url にブラウザをリダイレクトする
    （Stripe Checkout のホスト型決済ページ）。
    """
    checkout_url: str
    