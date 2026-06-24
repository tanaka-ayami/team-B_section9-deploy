"""
Firebase Admin SDKの初期化。
main.py の起動時に一度だけ呼ばれる。

サービスアカウントの読み込みは2パターンに対応する：
1. 環境変数 FIREBASE_CREDENTIALS_JSON にJSON文字列をそのまま入れる（推奨・.envで管理）
2. ローカルにファイルとして置く場合は FIREBASE_CREDENTIALS_PATH を指定する（開発時の代替手段）

.env / サービスアカウントJSONファイルはどちらも.gitignore対象。絶対にコミットしないこと。
"""
import json

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

_initialized = False


def init_firebase() -> None:
    global _initialized
    if _initialized:
        return

    if settings.FIREBASE_CREDENTIALS_JSON:
        # .envに1行で入れたJSON文字列をそのまま使う（推奨）
        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
    else:
        # ファイルパス指定の場合のフォールバック
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

    firebase_admin.initialize_app(cred)
    _initialized = True