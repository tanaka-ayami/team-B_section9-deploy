# API 設計書

> OpenAPI（Swagger）に準拠した形式で記述する。スキーマファイルは `backend/openapi.yaml` で管理し、本ドキュメントは概要、エンドポイント一覧、および運用ルールを示す。

---

## 1. 設計方針

- **スタイル**：REST API
- **認証方式**：Firebase IDトークンによるJWT認証。フロントエンドは HTTP ヘッダーに `Authorization: Bearer <Firebase_ID_Token>` を付与する。バックエンドは Firebase Admin SDK を用いてトークンを検証し、`users.firebase_uid` からユーザーを特定する。
- **バージョニング**：URL 埋め込み（`/v1/...`）
- **エラーレスポンスの共通フォーマット**：すべてのエラー（4xx, 5xx）は一意のエラーコードを含むJSON形式で統一する。

---

## 2. エンドポイント一覧

| メソッド | パス | 概要 | 認証 | 備考 |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/v1/auth/signup` | 新規ユーザー登録＆初期化 | 必要 | Firebase認証後、DBにユーザー作成＆個人グループと初期カテゴリを自動生成。 |
| GET | `/v1/users/me` | 自身のユーザー情報取得 | 必要 | 残りスキャン枚数やリマインド日数設定を含む。 |
| PATCH | `/v1/users/me` | リマインド日数等の設定更新 | 必要 | リマインド設定日数（N日前）を変更。 |
| POST | `/v1/documents/scan` | 書類画像のアップロード＆AI解析 | 必要 | 署名付きURL発行・OpenAI解析を実行（モック/失敗時は空を返す）。 |
| POST | `/v1/documents` | 書類データの最終登録 | 必要 | 解析確認画面からの登録。カレンダー即時反映＆リマインド生成。 |
| GET | `/v1/documents` | 書類一覧取得（カレンダー/期限なし） | 必要 | 所属グループの書類一覧（FullCalendar同期用・カテゴリ絞り込み可）。 |
| PATCH | `/v1/documents/{id}` | 書類編集 / 済スタンプON・OFF | 必要 | 済ONで `notification_schedules` を `cancelled` へ。 |
| DELETE | `/v1/documents/{id}` | 書類削除 | 必要 | 書類物理削除＆未送信リマインドを `cancelled` へ。 |
| GET | `/v1/notifications` | アプリ内お知らせ一覧取得 | 必要 | 他ユーザーが登録したお知らせを新着順で取得。 |
| PATCH | `/v1/notifications/{id}/read` | お知らせの既読化 | 必要 | お知らせを個別タップした際の既読更新用。 |
| POST | `/v1/groups` | 共有グループの新規作成 | 必要 | 家族などのグループ作成（作成者が `created_by` となる）。 |
| POST | `/v1/groups/{id}/invite` | グループへの招待発行 | 必要 | `invitations` レコードおよびSendGridで招待リンクを送信。 |

---

## 3. リクエスト / レスポンス例

### ① 新規ユーザー登録＆初期化 `POST /v1/auth/signup`

フロントエンドでFirebase Authのサインアップが完了した直後にコールする。バックエンド側で `users` レコードの作成、個人グループの自動生成、初期カテゴリのシーディングを一括で行う。

```http
POST /v1/auth/signup
Authorization: Bearer <Firebase_ID_Token>
Content-Type: application/json
```

```json
// Request Body（空オブジェクト、または初期プロファイル情報）
{}
```

```json
// Response Body (201 Created)
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "remind_days_before": 3,
    "plan_status": "free",
    "monthly_scan_count": 0
  },
  "personal_group": {
    "id": 101,
    "name": "user@example.com のマイグループ"
  }
}
```

---

### ② 書類画像のアップロード＆AI解析 `POST /v1/documents/scan`

スマホで撮影した画像（バイナリ）を受け取り、Cloudinaryへ保存して署名付きURLを発行後、OpenAI API（Structured Outputs）で解析した結果を返す。

```http
POST /v1/documents/scan
Authorization: Bearer <Firebase_ID_Token>
Content-Type: multipart/form-data

(file: binary data)
```

```json
// Response Body (200 OK)
{
  "image_url": "https://res.cloudinary.com/example/image/authenticated/s--abc--/v1/document.jpg",
  "ai_analysis": {
    "title": "遠足のお知らせ",
    "category": "学校",
    "deadline": "2026-07-01",
    "has_deadline": true
  }
}
```

---

### ③ 書類データの最終登録 `POST /v1/documents`

解析確認画面（UI-004）でユーザーが修正・確定したデータをDBへ登録する。登録完了に伴い、グループメンバーへのお知らせ（🔔）作成およびメールリマインドスケジュールが自動作成される。

```http
POST /v1/documents
Authorization: Bearer <Firebase_ID_Token>
Content-Type: application/json
```

```json
// Request Body
{
  "group_id": 101,
  "title": "遠足のお知らせ（修正済）",
  "category": "学校",
  "deadline_date": "2026-07-01",
  "has_deadline": true,
  "image_url": "https://res.cloudinary.com/example/image/authenticated/s--abc--/v1/document.jpg"
}
```

```json
// Response Body (201 Created)
{
  "id": 501,
  "group_id": 101,
  "title": "遠足のお知らせ（修正済）",
  "category": "学校",
  "deadline_date": "2026-07-01",
  "is_completed": false,
  "created_at": "2026-06-13T00:42:32Z"
}
```

---

### ④ 済スタンプの切り替え `PATCH /v1/documents/{id}`

詳細画面（UI-005）での「済スタンプ」のトグル操作を反映する。`is_completed: true` となった場合、バックエンド側で対象書類の `pending` 状態のリマインドを即座に `cancelled` へ更新する。

```http
PATCH /v1/documents/501
Authorization: Bearer <Firebase_ID_Token>
Content-Type: application/json
```

```json
// Request Body
{
  "is_completed": true
}
```

```json
// Response Body (200 OK)
{
  "id": 501,
  "is_completed": true,
  "message": "済スタンプが適用されました。未送信のリマインドメールはキャンセルされました。"
}
```

---

## 4. エラーレスポンス

エラー時は一律で HTTP ステータスコードを適切に分類し、以下の共通構造を持つ JSON を返却する。

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "ユーザー向けのエラーメッセージ、または詳細情報"
  }
}
```

### 主な共通エラーコード一覧

| HTTP ステータス | エラーコード（`code`） | 発生条件 / 理由 |
| :--- | :--- | :--- |
| 401 Unauthorized | `UNAUTHORIZED` | Firebase IDトークンが無効、期限切れ、または未設定。 |
| 403 Forbidden | `FORBIDDEN_GROUP_ACTION` | 他人のグループの書類へのアクセス、または作成者以外によるグループ削除操作。 |
| 404 Not Found | `RESOURCE_NOT_FOUND` | 指定された書類（`document_id`）やグループが存在しない。 |
| 422 Unprocessable | `SCAN_LIMIT_EXCEEDED` | 当月の無料スキャン上限（`monthly_scan_count`）を超過（Stripeへの導線トリガー）。 |
| 500 Internal Error | `OPENAI_API_FAILED` | OpenAI APIのエラーが指数バックオフ（3回リトライ）後も解消しなかった場合。 |

---

## 5. レート制限・冪等性

### レート制限の方針

- 一般的なAPIエンドポイント（GETなど）は、Redisを用いてユーザー（`firebase_uid`）あたり **1分間に最大 120リクエスト** に制限する。
- AI解析エンドポイント（`POST /v1/documents/scan`）は、OpenAI APIの負荷およびコスト管理の観点から、**1分間に最大 5リクエスト** の厳格な制限を設ける。

### POST / PATCH に対する冪等性の扱い

- **書類登録（`POST /v1/documents`）**：モバイル通信の瞬断等による重複登録を防ぐため、フロントエンドは画面遷移時に生成した一意のUUIDをヘッダー `X-Idempotency-Key` に付与して送信することを推奨とする。バックエンドは同一キーによる2重リクエストを検知した場合、初回と同じレスポンス（201）を即座に返却して多重インサートを防ぐ。
- **済スタンプ等の PATCH リクエスト**：状態の「上書き」であるため冪等キーは不要（何度リクエストしても最終的な状態は変わらないため）。