import os
import time
import logging

from openai import OpenAI

from app.schemas.document_analysis import DocumentAnalysis

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

SYSTEM_PROMPT = """
あなたは家庭や学校から届く書類（プリント）を解析するアシスタントです。
画像から以下の情報を抽出してください。

- title: 書類のタイトル（例：「遠足のお知らせ」）
- category: カテゴリ名（例：「学校」「医療」「行政」「保険」「その他」）。判断できない場合はnull
- deadline: 提出・支払いの期限日（ISO8601形式、例：「2026-07-01」）。期限がない、または読み取れない場合はnull
- has_deadline: 期限があるかどうかの真偽値。deadlineがnullでも「期限なし」と明示的に判断できる場合はfalse

「発行日」「作成日」「印刷日」などの書類の作成日付は期限ではありません。提出・支払い・申込等の締め切りが明示されている場合のみ deadline に設定してください。
「宛先」情報は抽出しないでください。
"""


def analyze_document_image(image_url: str, model: str | None = None) -> DocumentAnalysis | None:
    """
    書類画像をOpenAI APIに送り、Structured Outputsで情報を抽出する。
    解析に失敗した場合はNoneを返す。

    Args:
        image_url: 解析対象の画像URL（Cloudinaryの署名付きURL）
        model: 使用するモデル名。省略時は環境変数 OPENAI_MODEL を使用

    Returns:
        DocumentAnalysis | None: 解析結果。失敗時はNone
    """
    target_model = model or MODEL_NAME

    start_time = time.time()
    try:
        response = client.responses.parse(
            model=target_model,
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

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "openai.analysis_success",
            extra={
                "model": target_model,
                "durationMs": duration_ms,
                "title": response.output_parsed.title if response.output_parsed else None,
                "category": response.output_parsed.category if response.output_parsed else None,
                "hasDeadline": response.output_parsed.has_deadline if response.output_parsed else None,
            }
        )

        return response.output_parsed

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "openai.analysis_failed",
            extra={
                "model": target_model,
                "durationMs": duration_ms,
                "error": str(e),
            }
        )
        return None