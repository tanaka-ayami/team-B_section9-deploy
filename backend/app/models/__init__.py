"""
Alembicのenv.pyから `from app.models import *` 等で読み込めるように、
全モデルをここに集約しておく。
Alembic担当の方が来たら、このファイルをimportするだけでmetadataに全テーブルが乗る。
"""
from app.models.user import User, Group, GroupMember  # noqa: F401
from app.models.notification import Category, AppNotification, NotificationSchedule  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.invitation import Invitation  # noqa: F401

__all__ = [
    "User",
    "Group",
    "GroupMember",
    "Category",
    "AppNotification",
    "NotificationSchedule",
    "Document",
    "Invitation",
]