"""
documents（書類情報）
ER図（drawSQL）に厳密に合わせている。
category_idはNULL許容のため、categoriesが未実装でも書類登録・カレンダー表示は動作する
（issue #12の補足コメント通り）。
notification.pyのスタイルに合わせ、relationship()は使わずFKカラムのみで構成。
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    has_deadline: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_documents_group_id_deadline_date", "group_id", "deadline_date"),
    )