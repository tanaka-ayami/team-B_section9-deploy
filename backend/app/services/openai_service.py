import os
import time
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI

from app.schemas.document_analysis import DocumentAnalysis

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

SYSTEM_PROMPT_TEMPLATE = """
あなたは家庭や学校から届く書類（プリント）を解析するアシスタントです。
今日の日付は {today}（{weekday}）です。

抽出項目：
- title: 書類のタイトル（例：「遠足のお知らせ」）
- category: カテゴリ名（例：「学校」「医療」「行政」「保険」「その他」）。判断できない場合はnull
- deadline: 提出・支払い・申込の期限日（ISO8601形式）。ない場合はnull
- has_deadline: 期限の有無

【deadlineの最重要ルール】
deadlineに設定してよいのは、「まで」「までに」「締切」「〆切」「期限」「期日」「必着」など、締め切りを意味する言葉と一緒に書かれた日付だけです。
締め切りを意味する言葉を伴わない日付は、すべて期限ではありません。特に：
- 書類の右上やタイトル付近の日付は発行日・作成日であり、期限ではない
- 「実施日」「開催日」などイベントの日付も期限ではない
締め切りを意味する言葉が書類のどこにもない場合は、必ず deadline: null、has_deadline: false としてください。

例1：右上に「{example_year}年6月1日」、本文に締め切りの記載なし
→ deadline: null, has_deadline: false（右上の日付は発行日）

例2：本文に「7月1日（水）までにご提出ください」
→ deadline: "{example_year}-07-01", has_deadline: true

例3：「遠足実施日：7月10日（金）」のみで申込締切の記載なし
→ deadline: null, has_deadline: false（実施日は期限ではない）

【年の補完ルール】
- 期限に年の記載がない場合は今日の日付を基準に年を補完する
- 補完結果が今日より過去になる場合は翌年として解釈する
- 西暦・和暦（令和◯年など）が明記されていればその年を使う

「宛先」情報は抽出しないでください。
"""

_WEEKDAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _build_system_prompt(now: datetime | None = None) -> str:
    now = now or datetime.now(ZoneInfo("Asia/Tokyo"))
    return SYSTEM_PROMPT_TEMPLATE.format(
        today=now.strftime("%Y-%m-%d"),
        weekday=_WEEKDAYS_JA[now.weekday()],
        example_year=now.year,
    )


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
            temperature=0,  # 抽出タスクのため出力を決定的にする
            input=[
                {
                    "role": "system",
                    "content": _build_system_prompt(),
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