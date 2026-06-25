import shutil
import tempfile
import os
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.document import Document
from app.api.v1.notifications import get_current_db_user
from app.services.cloudinary_service import upload_document_image
from app.services.openai_service import analyze_document_image
from app.services.group_service import is_group_member
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
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        upload_result = upload_document_image(tmp_path)
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.remove(tmp_path)
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


class DocumentUpdate(BaseModel):
    category_id: UUID | None = None
    title: str | None = None
    has_deadline: bool | None = None
    deadline_date: date | None = None
    is_done: bool | None = None


def _document_to_dict(d: Document) -> dict:
    """Documentモデルをレスポンス用の辞書に変換する（共通処理）。"""
    return {
        "id": str(d.id),
        "group_id": str(d.group_id),
        "category_id": str(d.category_id) if d.category_id else None,
        "title": d.title,
        "image_url": d.image_url,
        "has_deadline": d.has_deadline,
        "deadline_date": d.deadline_date.isoformat() if d.deadline_date else None,
        "is_done": d.is_done,
        "created_by": str(d.created_by),
        "created_at": d.created_at.isoformat(),
    }


def _get_document_or_404(db: Session, document_id: UUID) -> Document:
    """document_idで書類を取得する。無ければ404を返す（共通処理）。"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="書類が見つかりません")
    return document


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
    if not is_group_member(db, payload.group_id, current_user.id):
        raise HTTPException(status_code=403, detail="このグループのメンバーではありません")

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
    db.flush()

    create_document_notifications(
        db=db,
        group_id=payload.group_id,
        document_id=document.id,
        created_by_user_id=current_user.id,
    )

    if payload.has_deadline and payload.deadline_date:
        create_reminder_schedules(
            db=db,
            group_id=payload.group_id,
            document_id=document.id,
            deadline_date=payload.deadline_date,
        )

    db.commit()

    return _document_to_dict(document)


@router.get("/v1/groups/{group_id}/documents")
def list_documents(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_db_user),
):
    """
    指定したグループの書類一覧を取得する。
    """
    if not is_group_member(db, group_id, current_user.id):
        raise HTTPException(status_code=403, detail="このグループのメンバーではありません")

    documents = db.query(Document).filter(Document.group_id == group_id).all()

    return {"documents": [_document_to_dict(d) for d in documents]}


@router.get("/v1/documents/{document_id}")
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_db_user),
):
    """
    書類1件の詳細を取得する。
    """
    document = _get_document_or_404(db, document_id)

    if not is_group_member(db, document.group_id, current_user.id):
        raise HTTPException(status_code=403, detail="このグループのメンバーではありません")

    return _document_to_dict(document)


@router.patch("/v1/documents/{document_id}")
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_db_user),
):
    """
    書類の内容を編集する。済スタンプ（is_done）のON/OFFもここで行う。
    """
    document = _get_document_or_404(db, document_id)

    if not is_group_member(db, document.group_id, current_user.id):
        raise HTTPException(status_code=403, detail="このグループのメンバーではありません")

    # 送られてきた項目だけを更新する（Noneのままの項目は変更しない）
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(document, key, value)

    db.commit()

    return _document_to_dict(document)


@router.delete("/v1/documents/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_db_user),
):
    """
    書類を削除する。
    """
    document = _get_document_or_404(db, document_id)

    if not is_group_member(db, document.group_id, current_user.id):
        raise HTTPException(status_code=403, detail="このグループのメンバーではありません")

    db.delete(document)
    db.commit()
    