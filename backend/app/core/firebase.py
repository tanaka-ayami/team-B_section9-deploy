"""
Firebase Admin SDKの初期化。
main.py の起動時に一度だけ呼ばれる。
サービスアカウントJSONは .gitignore 対象。各自Firebaseコンソールから取得して
backend/firebase-service-account.json に配置する（.env.exampleにパスを明記）。
"""
import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

_initialized = False


def init_firebase() -> None:
    global _initialized
    if _initialized:
        return
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    _initialized = True
