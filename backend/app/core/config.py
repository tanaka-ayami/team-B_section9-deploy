# backend/app/core/config.py
import os

if os.getenv("APP_ENV", "development") == "production":
    from app.core.config_prod import settings
else:
    from app.core.config_dev import settings

__all__ = ["settings"]