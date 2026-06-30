"""
課金API（issue #22）
- POST /v1/billing/checkout-session   Stripe Checkout セッションの作成
- POST /v1/billing/webhook            Stripe Webhook受信（決済完了時に plan_status を更新）

設計方針：
- カード情報は一切自前のサーバーで扱わない。Stripeがホストする決済ページ
  （Checkout Session）へリダイレクトする方式を採用する（PCI DSS対応の手間を回避）。
- 決済の成否は同期レスポンスではなく、Stripeから送られてくるWebhookイベントで
  確定させる（チェックアウトページ上でユーザーが離脱した場合などを考慮）。
"""
import stripe
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.v1.deps_db import get_current_user
from app.core.config import settings
from app.core.errors import APIError
from app.db.base import get_db
from app.models.user import User
from app.schemas.billing import CheckoutSessionRead

router = APIRouter(prefix="/billing", tags=["billing"])

stripe.api_key = settings.STRIPE_SECRET_KEY

# 決済完了後・キャンセル後にユーザーを戻すフロントエンドのURL。
# 本来は環境変数化が望ましいが、他のフロントURLもまだ.env管理されていないため
# 既存の構成に合わせて一旦ここに定義する（要・後続issueでの環境変数化検討）。
FRONTEND_BASE_URL = "http://localhost:3000"


@router.post(
    "/checkout-session",
    response_model=CheckoutSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    月間スキャン上限超過時の有料プラン導線（FR-011）。
    Stripe Checkout セッションを作成し、ユーザーをリダイレクトすべきURLを返す。
    """
    if current_user.plan_status == "premium":
        raise APIError(409, "ALREADY_PREMIUM", "既に有料プランに加入済みです")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": settings.STRIPE_PREMIUM_PRICE_ID, "quantity": 1}],
            success_url=f"{FRONTEND_BASE_URL}/settings?checkout=success",
            cancel_url=f"{FRONTEND_BASE_URL}/settings?checkout=cancel",
            # Webhook受信時、どのユーザーの決済かをStripe側のイベントから
            # 特定するために自社ユーザーIDを埋め込む。
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
        )
    except stripe.error.StripeError as e:
        raise APIError(502, "STRIPE_API_FAILED", f"Stripeとの通信に失敗しました: {e.user_message or str(e)}")

    return CheckoutSessionRead(checkout_url=session.url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Stripeからの決済完了イベントを受信し、plan_statusを'premium'へ更新する。
    認証不要（Stripe側からのサーバー間通信のため）。署名検証で正当性を担保する。
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise APIError(400, "INVALID_WEBHOOK_SIGNATURE", "Webhookの署名検証に失敗しました")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # StripeObject は dict() での変換が正しく動かないため、to_dict() を使う
        user_id = session.to_dict().get("client_reference_id")

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user is not None:
                user.plan_status = "premium"
                db.commit()

    # Stripeは2xx以外を返すと再送してくるため、未対応のイベント種別でも200を返す
    return {"received": True}