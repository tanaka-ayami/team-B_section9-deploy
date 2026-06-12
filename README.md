# team-B_section9
# 開発環境セットアップ

## 必要なもの
- Docker Desktop（最新版）
- Git

## Windowsの方へ：Docker Desktopのメモリ設定
デフォルトのままだとコンテナが起動しないことがあります。
Docker Desktop を開いて Settings → Resources → Memory を **4GB以上** に変更してください。

## 初回セットアップ
```bash
# 1. リポジトリをクローン
git clone ...

# 2. 環境変数ファイルを作成
cp .env.example .env
# .env を開いて、各自のAPIキーを入力してください

# 3. 起動
docker compose up -d
```

## 起動後にアクセスできる画面
| 画面 | URL |
|---|---|
| フロントエンド | http://localhost:3000 |
| バックエンドAPI（Swagger） | http://localhost:8000/docs |
| DB確認（Adminer） | http://localhost:8080 |
| Redis確認 | http://localhost:8081 |
Adminerのログイン情報：System: PostgreSQL / Server: db / User: appuser / Password: .envのPOSTGRES_PASSWORDの値

## よく使うコマンド
```bash
# 起動
docker compose up -d

# 停止
docker compose down

# ログ確認
docker compose logs -f

# イメージ再ビルド（Dockerfileやrequirements.txtを変更したとき）
docker compose down
docker compose build --no-cache
docker compose up -d

# DBマイグレーション
docker compose exec backend alembic upgrade head
```

## ファイルを変更したとき
| 変更内容 | 必要な対応 |
|---|---|
| Pythonのコード | 自動でリロードされます（何もしなくてOK） |
| フロントのコード | 自動でリロードされます（何もしなくてOK） |
| requirements.txt | `docker compose build --no-cache` が必要 |
| package.json | `docker compose build --no-cache` が必要 |
| compose.yaml | `docker compose down` してから `docker compose up -d` |
| DBのテーブル変更 | **チャットで事前告知**してから `docker compose down -v && docker compose up -d` |

## DBのテーブルを変更するときのルール
データが全部消えます。必ず事前にチャットで告知してください。
```bash
# データも含めて全リセット（告知してから実行）
docker compose down -v
docker compose up -d
docker compose exec backend alembic upgrade head
```

## .envに追加があったとき
新しい環境変数が追加されたら `.env.example` も必ず更新します。
各自 `.env` に追記してから `docker compose down && docker compose up -d` してください。