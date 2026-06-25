import shutil
import tempfile
import os
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.document import Document
from app.api.v1.notifications import get_current_db_user
from app.services.cloudinary_service import upload_document_image
from app.services.openai_service import analyze_document_image
from app.services.notification_service import (
    create_document_notifications,
    create_reminder_schedules,
)

router = APIRouter()


@router.post("/v1/documents/scan")
async def scan_document(file: UploadFile = File(...)):
    """
    書類画像を受け取り、Cloudinaryへ保存しつつOpenAIで内容を解析する。
    """
    tmp_path = None
    try:
        # 拡張子を維持した一時ファイルとして保存
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        upload_result = upload_document_image(tmp_path)
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.remove(tmp_path)
    # OpenAIで画像を解析する（失敗時はNoneが返る）
    analysis = analyze_document_image(upload_result["image_url"])
    return {
        "image_url": upload_result["image_url"],
        "ai_analysis": analysis.model_dump() if analysis else None,
    }


class DocumentCreate(BaseModel):
    group_id: UUID
    category_id: UUID | None = None
    title: str | None = None
    image_url: str
    has_deadline: bool = False
    deadline_date: date | None = None


@router.post("/v1/documents", status_code=201)
def create_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_db_user),
):
    """
    解析確認画面で確定した書類データを登録する。
    登録に伴い、グループメンバーへの通知・リマインド予約を自動生成する。
    """
    document = Document(
        group_id=payload.group_id,
        category_id=payload.category_id,
        title=payload.title,
        image_url=payload.image_url,
        has_deadline=payload.has_deadline,
        deadline_date=payload.deadline_date,
        created_by=current_user.id,
    )
    db.add(document)
    db.flush()  # documentのidを確定させる（まだコミットはしない）

    # 登録者以外のメンバーへ通知を作成
    create_document_notifications(
        db=db,
        group_id=payload.group_id,
        document_id=document.id,
        created_by_user_id=current_user.id,
    )

    # 期限がある場合のみ、リマインド予約を作成
    if payload.has_deadline and payload.deadline_date:
        create_reminder_schedules(
            db=db,
            group_id=payload.group_id,
            document_id=document.id,
            deadline_date=payload.deadline_date,
        )

    db.commit()

    return {
        "id": str(document.id),
        "group_id": str(document.group_id),
        "category_id": str(document.category_id) if document.category_id else None,
        "title": document.title,
        "has_deadline": document.has_deadline,
        "deadline_date": document.deadline_date.isoformat() if document.deadline_date else None,
        "is_done": document.is_done,
        "created_by": str(document.created_by),
        "created_at": document.created_at.isoformat(),
    }