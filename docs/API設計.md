# API設計書（v2.4）

データベース設計書（v1.4）および要件定義書（v7.6）との整合性を取って再設計したAPI設計書。

OpenAPI（Swagger）に準拠した形式で記述する。スキーマファイルは `backend/openapi.yaml` で管理し、本ドキュメントは概要、エンドポイント一覧、および運用ルールを示す。

> **v2.4での変更点**：issue #73対応。`users.email_notify_enabled` 追加に伴い、`GET /v1/users/me` のレスポンスおよび `PATCH /v1/users/me` のリクエストに `email_notify_enabled` を追加。あわせて `PATCH /v1/users/me` の仕様を明確化（`display_name` ・ `email_notify_enabled` はいずれも任意項目で、リクエストに含まれたフィールドのみ更新する部分更新方式）。
>
> **v2.3での変更点**：issue #62（招待フローE2E確認）にて、招待中一覧を取得するエンドポイントが存在しないことが判明したため新規追加。また、`GroupMemberRead`（v2.2で追加予定としていた`display_name`）の実装漏れが見つかり修正された。
>
> **v2.2での変更点**：`users.display_name`追加に伴い、ユーザー関連エンドポイントのレスポンス・リクエストを更新。
>
> **v2.1での変更点（再掲）**：カテゴリAPIの仕様を変更。カテゴリは固定11種類の共通カテゴリのみで運用することとし、`POST` / `PATCH` / `DELETE /categories` を廃止。`GET /categories` のみ提供する。また `DELETE /groups/{id}` の独自エラーコード `GROUP_DELETE_CONFLICT` を追加。

---

## 1. 設計方針

- **スタイル**：REST API
- **認証方式**：Firebase IDトークンによるJWT認証。
  - フロントエンドはHTTPヘッダーに `Authorization: Bearer <Firebase_ID_Token>` を付与する。
  - バックエンドはFirebase Admin SDKを用いてトークンを検証し、`users.firebase_uid` からユーザーを特定する（FR-001）。
- **バージョニング**：URL埋め込み（`/v1/...`）
- **識別子のデータ型**：DB設計書との整合性を担保するため、すべてのリソースID（`user_id`, `group_id`, `document_id`, `category_id` 等）には **UUID形式の文字列** を採用する。
- **権限モデル**：グループ内メンバーは一律同等権限（書類の登録・編集・削除が可能）。**グループ自体の削除のみ `groups.created_by` のユーザーに制限**する（要件定義書 4章・FR-002）。
  - カテゴリ（`categories`）は固定の共通データであり、権限モデルの対象外。管理者・一般メンバーを問わず、APIからの追加・編集・削除は一切提供しない。
- **エラーレスポンスの共通フォーマット**：すべてのエラー（4xx, 5xx）は一意のエラーコードを含むJSON形式で統一する。

```json
{
  "error": {
    "code": "FORBIDDEN_GROUP_ACTION",
    "message": "このグループの管理者のみ操作できます"
  }
}
```

---

## 2. エンドポイント一覧

### ユーザー・認証 【v2.4で変更】

| メソッド | パス              | 概要                     | 認証 | 備考                                                                                                                                                                                                                                                                                      |
| -------- | ----------------- | ------------------------ | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| POST     | `/v1/auth/signup` | 新規ユーザー登録＆初期化 | 必要 | Firebase認証後、`users` 作成＆「個人グループ」を自動生成（FR-001）。**`display_name`が必須項目として追加（v2.2）。** ⚠️ 入力経路（フォーム入力かFirebaseの表示名流用か）はBE①に確認必要。                                                                                                 |
| GET      | `/v1/users/me`    | 自身のユーザー情報取得   | 必要 | `display_name` / `plan_status` / `monthly_scan_count` / `remind_days_before` / **`email_notify_enabled`（v2.4で追加）** を含む。                                                                                                                                                          |
| PATCH    | `/v1/users/me`    | プロフィール・設定更新   | 必要 | `display_name` ・ **`email_notify_enabled`（v2.4で追加）** はいずれも任意項目。**部分更新方式**：リクエストボディに含まれたフィールドのみを更新し、含まれないフィールドは現状維持する（UI-006・UI-008）。`remind_days_before` の更新は本エンドポイントでは未対応（要確認・別issue管理）。 |

### グループ・招待 【メンバー一覧のみ変更】

| メソッド | パス                             | 概要                                | 認証 | 備考                                                                                                                                                                             |
| -------- | -------------------------------- | ----------------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET      | `/v1/groups`                     | 所属グループ一覧取得                | 必要 | 個人グループ・共有グループの両方を含む。                                                                                                                                         |
| POST     | `/v1/groups`                     | 共有グループの新規作成              | 必要 | 作成者は `created_by` に記録され、同時に `group_members` へ自動登録（FR-002）。                                                                                                  |
| DELETE   | `/v1/groups/{id}`                | グループ削除                        | 必要 | `created_by` のユーザーのみ実行可能。他メンバーは `403 FORBIDDEN_GROUP_ACTION`。紐づく `documents` / `categories` 等が残っており削除できない場合は `409 GROUP_DELETE_CONFLICT`。 |
| GET      | `/v1/groups/{id}/members`        | グループメンバー一覧取得            | 必要 | 設定画面（UI-006-G）でのメンバー表示用。レスポンスに `email` と **`display_name`（v2.2で追加）** を含む。                                                                        |
| POST     | `/v1/groups/{id}/invite`         | グループへの招待発行                | 必要 | `invitations` レコード作成＆SendGridで招待リンクを送信（FR-002）。                                                                                                               |
| GET      | `/v1/groups/{id}/invitations`    | グループの招待中（pending）一覧取得 | 必要 | グループ管理画面（UI-006-G）の「招待中」セクション用。`status='pending'`のみを`created_at`降順で返す。グループメンバーであれば誰でも参照可（招待発行者に限定しない）。           |
| GET      | `/v1/invitations/{token}`        | 招待情報の取得                      | 不要 | 招待ページ表示用（招待元・グループ名の確認）。期限切れでも200を返す（期限切れ表示はFE側で`expires_at`を見て判定）。                                                              |
| POST     | `/v1/invitations/{token}/accept` | 招待の承諾                          | 必要 | `group_members` へ追加し、`status` を `accepted` へ更新。期限切れは `410 INVITATION_EXPIRED`。処理済みは `409 INVITATION_ALREADY_HANDLED`。                                      |
| POST     | `/v1/invitations/{token}/reject` | 招待の拒否                          | 必要 | `status` を `rejected` へ更新。期限切れ・処理済みの場合のエラーはacceptと同様。                                                                                                  |

> 補足：画面設計書（UI-006-G）には `GET /v1/invitations?group_id=xxx` というクエリパラメータ形式のパスが記載されていたが、他のグループ配下リソース（`members`等）と一貫性を取るため、実装は `GET /v1/groups/{id}/invitations`（パスパラメータ形式）を正とする。画面設計書側の記載修正はFE担当の更新時に合わせて反映予定。

### カテゴリ

| メソッド | パス             | 概要             | 認証 | 備考                                                                                     |
| -------- | ---------------- | ---------------- | ---- | ---------------------------------------------------------------------------------------- |
| GET      | `/v1/categories` | カテゴリ一覧取得 | 必要 | 固定11種類の共通カテゴリ（`group_id IS NULL`）を返す。`icon`（絵文字）を含む（FR-010）。 |

> `POST` / `PATCH` / `DELETE /v1/categories` は廃止済み。カテゴリは固定運用のため、グループ管理者であっても追加・編集・削除は不可。

### 書類

| メソッド | パス                 | 概要                           | 認証 | 備考                                                                                                                                       |
| -------- | -------------------- | ------------------------------ | ---- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| POST     | `/v1/documents/scan` | 書類画像のアップロード＆AI解析 | 必要 | 署名付きURL発行＆OpenAI解析を実行（FR-003）。失敗時は `OPENAI_API_FAILED`（500）。フロントは空欄の確認画面を表示して手入力に誘導する。     |
| POST     | `/v1/documents`      | 書類データの最終登録           | 必要 | 解析確認画面からの登録（FR-004）。カレンダー即時反映＆各グループメンバー向けの `notification_schedules` / `app_notifications` を自動生成。 |
| GET      | `/v1/documents`      | 書類一覧取得                   | 必要 | `has_deadline` / `category_id` / `year` / `month` 等で絞り込み可能（カレンダー同期・期限なし書類一覧の両方に対応／FR-005, FR-007）。       |
| GET      | `/v1/documents/{id}` | 書類詳細取得                   | 必要 | 詳細画面（UI-005）用。                                                                                                                     |
| PATCH    | `/v1/documents/{id}` | 書類編集 / 済スタンプON・OFF   | 必要 | `is_done: true` で、関連する全ユーザーの `notification_schedules`（`status='pending'`）を `cancelled` へ一括更新（FR-006）。               |
| DELETE   | `/v1/documents/{id}` | 書類削除                       | 必要 | 物理削除。関連する `notification_schedules` / `app_notifications` も連動して削除（ON DELETE CASCADE）。                                    |

### アプリ内お知らせ

| メソッド | パス                          | 概要                     | 認証 | 備考                                                                      |
| -------- | ----------------------------- | ------------------------ | ---- | ------------------------------------------------------------------------- |
| GET      | `/v1/notifications`           | アプリ内お知らせ一覧取得 | 必要 | `created_at` 降順。登録した本人には自分の登録通知を表示しない（FR-009）。 |
| PATCH    | `/v1/notifications/{id}/read` | お知らせの既読化         | 必要 | 個別タップ時の既読更新用。                                                |

### 課金（Stripe）

| メソッド | パス                           | 概要                     | 認証             | 備考                                                                  |
| -------- | ------------------------------ | ------------------------ | ---------------- | --------------------------------------------------------------------- |
| POST     | `/v1/billing/checkout-session` | Stripe決済セッション作成 | 必要             | 月間スキャン上限超過時の有料プラン導線（FR-011）。                    |
| POST     | `/v1/billing/webhook`          | Stripe Webhook受信       | 不要（署名検証） | 決済完了イベントを受け、`users.plan_status` を `'premium'` 等へ更新。 |

---

## 3. リクエスト / レスポンス例

### ① 新規ユーザー登録＆初期化 `POST /v1/auth/signup`

Firebase Authのサインアップ完了直後にコールする。`users` レコード作成、個人グループの自動生成を一括で行う。
既に登録済みのユーザーが呼んだ場合は、新規作成せず既存のユーザー・グループ情報をそのまま返す（冪等）。

```http
POST /v1/auth/signup
Authorization: Bearer <Firebase_ID_Token>
Content-Type: application/json
```

```json
// Request Body
{
  "display_name": "山田太郎"
}
```

```json
// Response Body (201 Created)
{
  "user": {
    "id": "4a7b9c3d-e2f1-4b5a-8c9d-0e1f2a3b4c5d",
    "email": "user@example.com",
    "display_name": "山田太郎",
    "plan_status": "free",
    "monthly_scan_count": 0,
    "remind_days_before": 3
  },
  "personal_group": {
    "id": "8f7e6d5c-4b3a-2a1f-0e9d-8c7b6a5b4c3d",
    "name": "山田太郎"
  }
}
```

### ② 書類画像のアップロード＆AI解析 `POST /v1/documents/scan`

画像（バイナリ）を受け取り、Cloudinaryへ保存して署名付きURLを発行後、OpenAI APIで解析した結果を返す。「宛先」フィールドは解析対象外（要件定義書 FR-003）。

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

> `category` はカテゴリ名の文字列で返る（付録のStructured Outputsスキーマに準拠）。フロントエンドは `GET /v1/categories` の結果と名称マッチングして `category_id`（UUID）を解決し、③の登録APIに渡す。

### ③ 書類データの最終登録 `POST /v1/documents`

解析確認画面でユーザーが修正・確定したデータをDBへ登録する。登録に伴い、グループ内全ユーザー（各自の `remind_days_before` に応じたスケジュール）への `notification_schedules`、および本人以外のメンバーへの `app_notifications` が自動生成される。

```http
POST /v1/documents
Authorization: Bearer <Firebase_ID_Token>
Content-Type: application/json
```

```json
// Request Body
{
  "group_id": "8f7e6d5c-4b3a-2a1f-0e9d-8c7b6a5b4c3d",
  "category_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "title": "遠足のお知らせ（修正済）",
  "has_deadline": true,
  "deadline_date": "2026-07-01",
  "image_url": "https://res.cloudinary.com/example/image/authenticated/s--abc--/v1/document.jpg"
}
```

```json
// Response Body (201 Created)
{
  "id": "2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
  "group_id": "8f7e6d5c-4b3a-2a1f-0e9d-8c7b6a5b4c3d",
  "category_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "title": "遠足のお知らせ（修正済）",
  "has_deadline": true,
  "deadline_date": "2026-07-01",
  "is_done": false,
  "created_by": "4a7b9c3d-e2f1-4b5a-8c9d-0e1f2a3b4c5d",
  "created_at": "2026-06-22T00:42:32Z"
}
```

### ④ 済スタンプの切り替え `PATCH /v1/documents/{id}`

詳細画面（UI-005）での「済スタンプ」トグル操作を反映する。`is_done: true` の場合、対象書類に関連するすべての送信予定リマインド（`notification_schedules` 内の `status: 'pending'`）を即座に `cancelled` へ更新する。

```http
PATCH /v1/documents/2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e
Authorization: Bearer <Firebase_ID_Token>
Content-Type: application/json
```

```json
// Request Body
{
  "is_done": true
}
```

```json
// Response Body (200 OK)
{
  "id": "2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
  "is_done": true,
  "message": "済スタンプが適用されました。未送信のリマインドメールはキャンセルされました。"
}
```

### ⑤ グループ招待の発行と承諾 `POST /v1/groups/{id}/invite` → `POST /v1/invitations/{token}/accept`

招待発行時、`invitations` レコードを作成し、SendGridで招待リンク（`token` を含むURL）を送信する。

```http
POST /v1/groups/8f7e6d5c-4b3a-2a1f-0e9d-8c7b6a5b4c3d/invite
Authorization: Bearer <Firebase_ID_Token>
Content-Type: application/json
```

```json
// Request Body
{
  "invitee_email": "family@example.com"
}
```

---

## 3.5. スキーマ定義（v2.4での変更分）

```jsonc
// UserRead（GET /v1/users/me）
{
  "id": "uuid",
  "firebase_uid": "string",
  "email": "string",
  "display_name": "string",   // 【v2.2で追加】
  "plan_status": "string",
  "monthly_scan_count": "integer",
  "remind_days_before": "integer",
  "email_notify_enabled": "boolean"   // 【v2.4で追加】true: メール+アプリ内通知 / false: アプリ内通知のみ
}

// UserUpdate（PATCH /v1/users/me のリクエストボディ）
// 【v2.4で追加】display_name・email_notify_enabledはいずれも任意（Optional）。
// リクエストに含まれたフィールドのみを更新する部分更新方式。
{
  "display_name": "string?",            // 任意。指定時は1〜50文字
  "email_notify_enabled": "boolean?"    // 任意
}

// GroupMemberRead（GET /v1/groups/{id}/members）
{
  "id": "uuid",
  "group_id": "uuid",
  "user_id": "uuid",
  "email": "string",
  "display_name": "string",   // 【v2.2で追加】
  "joined_at": "datetime"
}

// CategoryRead（GET /v1/categories）※変更なし
{
  "id": "uuid",
  "group_id": null,
  "name": "string",
  "color_code": "string | null",
  "icon": "string | null"
}

// InvitationRead（POST /v1/groups/{id}/invite のレスポンス、および GET /v1/groups/{id}/invitations の各要素）
{
  "id": "uuid",
  "group_id": "uuid",
  "invited_by": "uuid",
  "invitee_email": "string",
  "status": "pending | accepted | rejected",
  "created_at": "datetime",
  "expires_at": "datetime"
}
```

---

## 4. エラーコード一覧（抜粋）

> ⚠️ 本書のエラーコード一覧表は完全版が別途存在する想定です。以下はissue #16対応で追加されたコードのみを記載しています。既存の一覧表に追記してください。

| コード                       | HTTPステータス | 説明                                                                                                                       |
| ---------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `UNAUTHORIZED`               | 401            | Firebase IDトークンが無効、期限切れ、または未設定。                                                                        |
| `FORBIDDEN_GROUP_ACTION`     | 403            | 作成者（`created_by`）以外によるグループ削除操作、または共通カテゴリの編集・削除操作。グループ管理者限定操作の試行も含む。 |
| `GROUP_DELETE_CONFLICT`      | 409            | グループに紐づく `documents` 等が残っており削除できない                                                                    |
| `RESOURCE_NOT_FOUND`         | 404            | 指定された書類（`document_id`）、グループ、カテゴリ、招待等が存在しない。                                                  |
| `INVITATION_EXPIRED`         | 410            | `invitations.expires_at` を過ぎた招待トークンへのアクセス。                                                                |
| `INVITATION_ALREADY_HANDLED` | 409            | 既に承諾・拒否済みの招待への再操作                                                                                         |
| `SCAN_LIMIT_EXCEEDED`        | 422            | 当月の無料スキャン上限（`monthly_scan_count`）を超過（Stripeへの導線トリガー）。                                           |
| `OPENAI_API_FAILED`          | 500            | OpenAI APIのエラーが指数バックオフ（最大3回リトライ）後も解消しなかった場合。                                              |

---

## 5. レート制限・冪等性

### レート制限の方針

- 一般的なAPIエンドポイント（GETなど）は、Redisを用いてユーザー（`firebase_uid`）あたり **1分間に最大120リクエスト** に制限する。
- AI解析エンドポイント（`POST /v1/documents/scan`）は、OpenAI APIの負荷およびコスト管理の観点から、**1分間に最大5リクエスト** の厳格な制限を設ける。

### POST / PATCH に対する冪等性の扱い

- **書類登録（`POST /v1/documents`）**：モバイル通信の瞬断等による重複登録を防ぐため、フロントエンドは画面遷移時に生成した一意のUUIDをヘッダー `X-Idempotency-Key` に付与して送信することを推奨とする。バックエンドは同一キーによる2重リクエストを検知した場合、初回と同じレスポンス（201）を即座に返却する。
- **済スタンプ等のPATCHリクエスト**：状態の「上書き」であるため冪等キーは不要（何度リクエストしても最終的な状態は変わらないため）。
- **Stripe Webhook（`POST /v1/billing/webhook`）**：Stripeが送信する `event.id` を用いて重複イベント処理を防止する（同一イベントの再送に対して二重課金処理が起きないようにする）。

---

## 既知の課題（v2.4時点）

| 項目                                    | 内容                                                                                                                                                                                                                                                                                                                                                                                     |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 招待受諾時の本人確認の欠落              | `POST /v1/invitations/{token}/accept` は、トークンの有効性のみを検証し、「ログイン中のユーザーのメールアドレス」と「`invitations.invitee_email`」の一致確認を行っていない。トークンを知っている任意のユーザーが参加できてしまう。issue化済み（要対応）。                                                                                                                                 |
| `remind_days_before` の更新手段が未確認 | 設定画面（UI-006）には「期限の[N]日前にメール送信」という日数入力欄が存在し、画面設計書・要件定義書では `PATCH /v1/users/me` での更新を想定する記載がある。しかし issue #73 時点のバックエンド実装（`UserUpdate`）では `display_name` ・ `email_notify_enabled` のみが受け付け可能で、`remind_days_before` の更新ロジックが存在しない。意図的な未実装か実装漏れか要確認（issue化検討）。 |
