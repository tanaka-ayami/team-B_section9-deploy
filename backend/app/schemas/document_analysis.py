from pydantic import BaseModel
from typing import Optional


class DocumentAnalysis(BaseModel):
    """
    OpenAI Structured Outputsで使うレスポンスのスキーマ。
    書類画像から抽出する4項目を定義する。
    """
    title: str
    category: Optional[str] = None
    deadline: Optional[str] = None  # ISO8601形式（例: "2026-07-01"）
    has_deadline: bool
