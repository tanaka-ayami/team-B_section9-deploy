import os
from openai import OpenAI

from app.schemas.document_analysis import DocumentAnalysis

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = """
あなたは家庭や学校から届く書類（プリント）を解析するアシスタントです。
画像から以下の情報を抽出してください。

- title: 書類のタイトル（例：「遠足のお知らせ」）
- category: カテゴリ名（例：「学校」「医療」「行政」「保険」「その他」）。判断できない場合はnull
- deadline: 提出・支払いの期限日（ISO8601形式、例：「2026-07-01」）。期限がない、または読み取れない場合はnull
- has_deadline: 期限があるかどうかの真偽値。deadlineがnullでも「期限なし」と明示的に判断できる場合はfalse

「宛先」情報は抽出しないでください。
"""


def analyze_document_image(image_url: str) -> DocumentAnalysis | None:
    """
    書類画像をOpenAI APIに送り、Structured Outputsで情報を抽出する。
    解析に失敗した場合はNoneを返す。

    Args:
        image_url: 解析対象の画像URL（Cloudinaryの署名付きURL）

    Returns:
        DocumentAnalysis | None: 解析結果。失敗時はNone
    """
    try:
        response = client.responses.parse(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": image_url,
                        }
                    ],
                },
            ],
            text_format=DocumentAnalysis,
        )
        return response.output_parsed

    except Exception as e:
        print(f"[OpenAI解析エラー] {e}")
        return None
