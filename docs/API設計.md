# API設計書（v2.3）

データベース設計書（v1.3）および要件定義書（v7.5）との整合性を取って再設計したAPI設計書。

OpenAPI（Swagger）に準拠した形式で記述する。スキーマファイルは `backend/openapi.yaml` で管理し、本ドキュメントは概要、エンドポイント一覧、および運用ルールを示す。

> **v2.3での変更点**：書類一覧取得APIの実際のエンドポイントが `GET /v1/documents`（クエリパラメータで group_id 指定）ではなく `GET /v1/groups/{group_id}/documents`（パスパラメータ形式）として実装されていることが判明したため、本書の記載を実装に合わせて修正（issue #71対応時に発覚）。あわせてレスポンス形式（`{ documents: Document[] }`、`categoryName` 解決済み）を明記。
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

### ユーザー・認証 【v2.2で変更】

| メソッド | パス | 概要 | 認証 | 備考 |
|---|---|---|---|---|
| POST | `/v1/auth/signup` | 新規ユーザー登録＆初期化 | 必要 | Firebase認証後、`users` 作成＆「個人グループ」を自動生成（FR-001）。**`display_name`が必須項目として追加（v2.2）。** ⚠️ 入力経路（フォーム入力かFirebaseの表示名流用か）はBE①に確認必要。 |
| GET | `/v1/users/me` | 自身のユーザー情報取得 | 必要 | `display_name` / `plan_status` / `monthly_scan_count` / `remind_days_before` を含む（v2.2で`display_name`を追加）。 |
| PATCH | `/v1/users/me` | プロフィール・設定更新 | 必要 | `remind_days_before` に加え、**`display_name`の変更も可能（v2.2で追加）**（UI-006）。 |

### グループ・招待 【メンバー一覧のみ変更】

| メソッド | パス | 概要 | 認証 | 備考 |
|---|---|---|---|---|
| GET | `/v1/groups` | 所属グループ一覧取得 | 必要 | 個人グループ・共有グループの両方を含む。 |
| POST | `/v1/groups` | 共有グループの新規作成 | 必要 | 作成者は `created_by` に記録され、同時に `group_members` へ自動登録（FR-002）。 |
| DELETE | `/v1/groups/{id}` | グループ削除 | 必要 | `created_by` のユーザーのみ実行可能。他メンバーは `403 FORBIDDEN_GROUP_ACTION`。紐づく `documents` / `categories` 等が残っており削除できない場合は `409 GROUP_DELETE_CONFLICT`。 |
| GET | `/v1/groups/{id}/members` | グループメンバー一覧取得 | 必要 | 設定画面（UI-006-G）でのメンバー表示用。レスポンスに `email` と **`display_name`（v2.2で追加）** を含む。 |
| POST | `/v1/groups/{id}/invite` | グループへの招待発行 | 必要 | `invitations` レコード作成＆SendGridで招待リンクを送信（FR-002）。 |
| GET | `/v1/invitations/{token}` | 招待情報の取得 | 不要 | 招待ページ表示用（招待元・グループ名の確認）。期限切れでも200を返す（期限切れ表示はFE側で`expires_at`を見て判定）。 |
| POST | `/v1/invitations/{token}/accept` | 招待の承諾 | 必要 | `group_members` へ追加し、`status` を `accepted` へ更新。期限切れは `410 INVITATION_EXPIRED`。処理済みは `409 INVITATION_ALREADY_HANDLED`。 |
| POST | `/v1/invitations/{token}/reject` | 招待の拒否 | 必要 | `status` を `rejected` へ更新。期限切れ・処理済みの場合のエラーはacceptと同様。 |

### カテゴリ

| メソッド | パス | 概要 | 認証 | 備考 |
|---|---|---|---|---|
| GET | `/v1/categories` | カテゴリ一覧取得 | 必要 | 固定11種類の共通カテゴリ（`group_id IS NULL`）を返す。`icon`（絵文字）を含む（FR-010）。 |

> `POST` / `PATCH` / `DELETE /v1/categories` は廃止済み。カテゴリは固定運用のため、グループ管理者であっても追加・編集・削除は不可。

### 書類

| メソッド | パス | 概要 | 認証 | 備考 |
|---|---|---|---|---|
| POST | `/v1/documents/scan` | 書類画像のアップロード＆AI解析 | 必要 | 署名付きURL発行＆OpenAI解析を実行（FR-003）。失敗時は `OPENAI_API_FAILED`（500）。フロントは空欄の確認画面を表示して手入力に誘導する。 |
| POST | `/v1/documents` | 書類データの最終登録 | 必要 | 解析確認画面からの登録（FR-004）。カレンダー即時反映＆各グループメンバー向けの `notification_schedules` / `app_notifications` を自動生成。 |
| GET | `/v1/groups/{group_id}/documents` | 書類一覧取得 | 必要 | パスパラメータで対象グループを指定。`category_id` / `has_deadline` をクエリパラメータで指定すると絞り込み可能（issue #54：カレンダー同期・期限なし書類一覧・UI-007の絞り込みpillに対応／FR-005, FR-007）。レスポンスは `{ documents: Document[] }` 形式で、各 `Document` にはカテゴリ名を解決済みの `categoryName` を含む。 |
| GET | `/v1/documents/{id}` | 書類詳細取得 | 必要 | 詳細画面（UI-005）用。 |
| PATCH | `/v1/documents/{id}` | 書類編集 / 済スタンプON・OFF | 必要 | `is_done: true` で、関連する全ユーザーの `notification_schedules`（`status='pending'`）を `cancelled` へ一括更新（FR-006）。 |
| DELETE | `/v1/documents/{id}` | 書類削除 | 必要 | 物理削除。関連する `notification_schedules` / `app_notifications` も連動して削除（ON DELETE CASCADE）。 |

### アプリ内お知らせ

| メソッド | パス | 概要 | 認証 | 備考 |
|---|---|---|---|---|
| GET | `/v1/notifications` | アプリ内お知らせ一覧取得 | 必要 | `created_at` 降順。登録した本人には自分の登録通知を表示しない（FR-009）。 |
| PATCH | `/v1/notifications/{id}/read` | お知らせの既読化 | 必要 | 個別タップ時の既読更新用。 |

### 課金（Stripe）

| メソッド | パス | 概要 | 認証 | 備考 |
|---|---|---|---|---|
| POST | `/v1/billing/checkout-session` | Stripe決済セッション作成 | 必要 | 月間スキャン上限超過時の有料プラン導線（FR-011）。 |
| POST | `/v1/billing/webhook` | Stripe Webhook受信 | 不要（署名検証） | 決済完了イベントを受け、`users.plan_status` を `'premium'` 等へ更新。 |

---

## 3. スキーマ定義（v2.2での変更分）

```jsonc
// UserRead（GET /v1/users/me）
{
  "id": "uuid",
  "firebase_uid": "string",
  "email": "string",
  "display_name": "string",   // 【v2.2で追加】
  "plan_status": "string",
  "monthly_scan_count": "integer",
  "remind_days_before": "integer"
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
```

---

## 4. エラーコード一覧（抜粋）

> ⚠️ 本書のエラーコード一覧表は完全版が別途存在する想定です。以下はissue #16対応で追加されたコードのみを記載しています。既存の一覧表に追記してください。

| コード | HTTPステータス | 説明 |
|---|---|---|
| `FORBIDDEN_GROUP_ACTION` | 403 | グループ管理者（`created_by`）以外による、管理者限定操作（グループ削除等）の試行 |
| `GROUP_DELETE_CONFLICT` | 409 | グループに紐づく `documents` 等が残っており削除できない |
| `INVITATION_EXPIRED` | 410 | 招待の有効期限切れ |
| `INVITATION_ALREADY_HANDLED` | 409 | 既に承諾・拒否済みの招待への再操作 |
| `RESOURCE_NOT_FOUND` | 404 | 指定したリソース（グループ・カテゴリ・招待等）が存在しない |