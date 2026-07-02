"""
OpenAIモデル比較検証スクリプト（issue #56）
同じ書類画像を複数のモデルで解析し、精度・速度を比較する。

使い方：
  docker compose exec backend python scripts/compare_models.py <画像URL>

例：
  docker compose exec backend python scripts/compare_models.py \
    "https://res.cloudinary.com/example/image/authenticated/s--abc--/v1/document.jpg"
"""
import sys
import time
import os

from openai import OpenAI
from app.schemas.document_analysis import DocumentAnalysis

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
あなたは家庭や学校から届く書類（プリント）を解析するアシスタントです。
画像から以下の情報を抽出してください。

- title: 書類のタイトル（例：「遠足のお知らせ」）
- category: カテゴリ名（例：「学校」「医療」「行政」「保険」「その他」）。判断できない場合はnull
- deadline: 提出・支払いの期限日（ISO8601形式、例：「2026-07-01」）。期限がない、または読み取れない場合はnull
- has_deadline: 期限があるかどうかの真偽値。deadlineがnullでも「期限なし」と明示的に判断できる場合はfalse

「宛先」情報は抽出しないでください。
"""

# 検証対象モデル
MODELS = [
    "gpt-4o-mini",
    "gpt-4.1-nano",
    "gpt-5-nano",
]


def analyze_with_model(image_url: str, model: str) -> dict:
    """指定モデルで画像を解析し、結果と処理時間を返す。"""
    start = time.time()
    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [{"type": "input_image", "image_url": image_url}],
                },
            ],
            text_format=DocumentAnalysis,
        )
        duration_ms = int((time.time() - start) * 1000)
        result = response.output_parsed
        return {
            "model": model,
            "status": "success",
            "duration_ms": duration_ms,
            "title": result.title if result else None,
            "category": result.category if result else None,
            "deadline": result.deadline if result else None,
            "has_deadline": result.has_deadline if result else None,
            "error": None,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "model": model,
            "status": "error",
            "duration_ms": duration_ms,
            "title": None,
            "category": None,
            "deadline": None,
            "has_deadline": None,
            "error": str(e),
        }


def print_results(results: list[dict]) -> None:
    """結果を表形式で出力する。"""
    print("\n" + "=" * 70)
    print("OpenAIモデル比較検証結果")
    print("=" * 70)

    for r in results:
        print(f"\n【{r['model']}】")
        print(f"  ステータス   : {r['status']}")
        print(f"  処理時間     : {r['duration_ms']} ms")
        if r["status"] == "success":
            print(f"  タイトル     : {r['title']}")
            print(f"  カテゴリ     : {r['category']}")
            print(f"  期限         : {r['deadline']}")
            print(f"  期限あり     : {r['has_deadline']}")
        else:
            print(f"  エラー       : {r['error']}")

    print("\n" + "=" * 70)
    print("処理時間まとめ")
    print("=" * 70)
    for r in results:
        status_label = "✅" if r["status"] == "success" else "❌"
        print(f"  {status_label} {r['model']:<20} {r['duration_ms']:>6} ms")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python scripts/compare_models.py <画像URL>")
        sys.exit(1)

    image_url = sys.argv[1]
    print(f"解析対象URL: {image_url}")
    print(f"検証モデル: {', '.join(MODELS)}")
    print("\n解析中...")

    results = []
    for model in MODELS:
        print(f"  {model} を解析中...")
        result = analyze_with_model(image_url, model)
        results.append(result)

    print_results(results)