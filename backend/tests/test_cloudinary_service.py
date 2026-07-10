"""
cloudinary_service.py のユニットテスト（Cloudinary本体との通信は行わず、
cloudinary.uploader.upload / cloudinary.utils.cloudinary_url をモック化する）。
docker compose exec backend pytest tests/test_cloudinary_service.py -v で実行確認用。
"""
from unittest.mock import patch

from app.services import cloudinary_service


def test_upload_document_image_returns_signed_url_and_public_id():
    """アップロード結果から、署名付きURLとpublic_idを含む辞書が返ること。"""
    fake_upload_result = {"public_id": "documents/abc123"}

    with patch.object(
        cloudinary_service.cloudinary.uploader,
        "upload",
        return_value=fake_upload_result,
    ) as mock_upload, patch.object(
        cloudinary_service.cloudinary.utils,
        "cloudinary_url",
        return_value=("https://res.cloudinary.com/example/documents/abc123.webp", {}),
    ) as mock_url:
        result = cloudinary_service.upload_document_image("/tmp/dummy.jpg")

    mock_upload.assert_called_once_with(
        "/tmp/dummy.jpg",
        folder="documents",
        format="webp",
        type="authenticated",
    )
    mock_url.assert_called_once()

    assert result["public_id"] == "documents/abc123"
    assert result["image_url"] == "https://res.cloudinary.com/example/documents/abc123.webp"