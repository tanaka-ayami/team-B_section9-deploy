"""
ER図（drawSQL）に厳密に合わせている。
categories: group_idはnull許容（未分類カテゴリ等の運用に対応）。
  group_id=NULLの5件（学校・医療・行政・保険・その他）は起動時シーディング対象（app/db/seed.py参照）。
app_notifications: 書類登録時にdocuments API内でINSERTする想定（BE②はSELECT/PATCHのみ）。
  group_id（誰に届くかの判定用）とtriggered_by（誰の操作で発生したか）を分けて持つ。
  document_idはdocuments作成と同じPRで対応したため、ON DELETE CASCADEのFK制約を付与済み。
notification_schedules: メールリマインド管理（issue #12 MVP外チェックリスト対応）。
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color_code: Mapped[str | None] = mapped_column(String(7), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 絵文字を想定（issue #16後の追加変更）

class AppNotification(Base):
    __tablename__ = "app_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    triggered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_app_notifications_group_id_created_at", "group_id", "created_at"),
    )


class NotificationSchedule(Base):
    __tablename__ = "notification_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/sent/failed/cancelled
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_notification_schedules_scheduled_for_status", "scheduled_for", "status"),
        Index("ix_notification_schedules_user_id", "user_id"),
    )