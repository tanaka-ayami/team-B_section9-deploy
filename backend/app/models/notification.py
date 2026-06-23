"""
ER図（drawSQL）に厳密に合わせている。
categories: group_idはnull許容（未分類カテゴリ等の運用に対応）
app_notifications: 書類登録時にdocuments API内でINSERTする想定（BE②はSELECT/PATCHのみ）。
  group_id（誰に届くかの判定用）とtriggered_by（誰の操作で発生したか）を分けて持つ。
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
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
    # documents テーブルはBE①が後でCRUD APIと一緒に定義する想定。
    # 先にdocument_idカラムだけ確保しておき、FK制約は documents 作成後にAlembicの追加マイグレーションで付ける。
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_app_notifications_group_id_created_at", "group_id", "created_at"),
    )