import cloudinary.uploader
import cloudinary.utils


def upload_document_image(file_path: str) -> dict:
    """
    書類画像をCloudinaryにアップロードし、署名付きURLを発行する。

    Args:
        file_path: 一時保存された画像ファイルのパス

    Returns:
        dict: image_url（署名付きURL）と public_id を含む辞書
    """
    result = cloudinary.uploader.upload(
        file_path,
        folder="documents",
        format="webp",          # BE①からの提案を反映
        type="authenticated",   # 署名付きURL用の保存タイプ
    )

    # 署名付きURLを生成（1時間だけ有効）
    signed_url, _ = cloudinary.utils.cloudinary_url(
        result["public_id"],
        type="authenticated",
        sign_url=True,
        format="webp",
    )

    return {
        "image_url": signed_url,
        "public_id": result["public_id"],
    }
