"""
docker compose exec backend pytest app/tests/test_categories.py -v で実行確認用。
カテゴリは固定11種類の共通カテゴリのみで運用する方針（issue #16クローズ後の最終仕様）。
追加・編集・削除APIは提供しないため、一覧取得のテストのみ残す。
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_CATEGORY_NAMES = {
    "学校", "医療", "行政", "保険", "税金",
    "住居・暮らし", "子育て", "介護", "仕事", "趣味", "その他",
}


def test_list_categories_returns_fixed_eleven(user_a, login_as):
    with login_as(user_a):
        res = client.get("/v1/categories")
        assert res.status_code == 200

        categories = res.json()
        assert {c["name"] for c in categories} == EXPECTED_CATEGORY_NAMES
        assert all(c["group_id"] is None for c in categories)
        assert all(c["icon"] for c in categories)  # 全件にiconが入っているか


def test_list_categories_requires_auth():
    res = client.get("/v1/categories")
    assert res.status_code == 401