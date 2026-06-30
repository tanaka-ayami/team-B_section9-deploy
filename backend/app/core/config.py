"""
アプリ全体の設定を環境変数から読み込む。
.env は compose.yaml の env_file で渡される想定。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL（Alembic担当の方が来るまでは未使用でもOK）
    POSTGRES_USER: str = "appuser"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "appdb"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Firebase Admin SDK
    # 推奨：サービスアカウントJSONの内容をそのまま1行で.envに入れる
    FIREBASE_CREDENTIALS_JSON: str = ""
    # 代替：ファイルとして配置する場合のパス（JSONが未設定の場合のみ使用）
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"

    # Stripe（issue #22）
    # サンドボックス（テストモード）のキーを使用。本番移行時は live キーに差し替える。
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    # Webhookエンドポイント登録後にStripeダッシュボードで発行される署名検証用シークレット。
    # エンドポイント未登録の間は空のままでよい。
    STRIPE_WEBHOOK_SECRET: str = ""
    # 有料プラン（プレミアムプラン）の価格ID。Stripeダッシュボードの商品カタログで事前作成。
    # 価格改定時はダッシュボード側で新しいPriceを作成し、ここを差し替えるだけで済む。
    STRIPE_PREMIUM_PRICE_ID: str = ""


settings = Settings()