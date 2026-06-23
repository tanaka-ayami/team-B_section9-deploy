import shutil
import tempfile
import os

from fastapi import APIRouter, UploadFile, File

from app.services.cloudinary_service import upload_document_image
from app.services.openai_service import analyze_document_image

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
