import shutil
import tempfile
import os

from fastapi import APIRouter, UploadFile, File

from app.services.cloudinary_service import upload_document_image

router = APIRouter()


@router.post("/v1/documents/scan")
async def scan_document(file: UploadFile = File(...)):
    """
    書類画像を受け取り、Cloudinaryにアップロードして署名付きURLを返す。
    AI解析（OpenAI）はこの時点では未実装。issue #19で追加予定。
    """
    # 拡張子を維持した一時ファイルとして保存
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = upload_document_image(tmp_path)
    finally:
        # 一時ファイルを必ず削除する
        os.remove(tmp_path)

    return {
        "image_url": result["image_url"],
        "ai_analysis": None  # issue #19で実装予定
    }
