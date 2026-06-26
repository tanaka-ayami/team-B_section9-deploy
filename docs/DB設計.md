# データベース設計書（v1.2）

## 変更履歴

| バージョン | 変更内容 |
|---|---|
| v1.0 | 初版 |
| v1.1 | レビュー指摘事項を反映。①`notification_schedules.user_id` の役割（送信先特定ロジック）を明記、②`users` テーブルの管理カラムを再確認・強調、③主キー方針が **UUID** であることを明記（`bigint` ではない） |
| v1.2 | `categories` テーブルに `icon`（VARCHAR(20)）カラムを追加。初期シードデータを5種→11種に拡張。カテゴリAPIの仕様変更（追加・編集・削除API廃止）に伴い、`categories.group_id` は実質的に常にNULLとなる運用に変更 |
| **v1.3** | **`users` テーブルに `display_name`（VARCHAR(50), NOT NULL）を追加（BE①提案・決定事項・プッシュ済み）。グループメンバー一覧（`GET /v1/groups/{id}/members`）等での表示名として使用する（最新版）** |

---

## 0. レビュー指摘事項への回答（補足）

### ① notification_schedules の宛先（user_id）について
`notification_schedules` には **`user_id`（`users.id` への外部キー）** を保持しており、これが「誰に送るか」を示すカラムである。メールアドレスそのものは持たせず、Celery Workerが処理時に `user_id` → `users.id` → `users.email` の経路でメールアドレスを取得し送信する。

これは、ユーザーが後からメールアドレスを変更した場合でも、過去に生成済みのリマインドタスクが常に最新の送信先を参照できるようにするための設計である（メールアドレスをスナップショットとしてコピーしない）。

### ② users テーブルの不足カラムについて
`plan_status` / `monthly_scan_count` / `remind_days_before` / **`display_name`（v1.3で追加）** の4カラムは `users` テーブルに含まれている（3.1節参照）。API設計書の `GET /v1/users/me`（取得）・`PATCH /v1/users/me`（更新）が対応するエンドポイントであり、別テーブルでの管理は行わない。

### ③ 主キーの型について
全テーブルの主キーは **UUID（`gen_random_uuid()`）** で統一する。`bigint`（連番）は採用しない。

理由：
- 要件定義書およびER図との整合性を保つため。
- 将来的な分散環境・複数インスタンスでのID生成競合を避けるため。
- URLやAPIレスポンスにIDをそのまま含めても、連番のように全体件数や成長速度を推測されない（推測可能性の低減）。

### ④ categories.group_id カラムを残す理由について
カテゴリAPIの仕様変更により、`categories.group_id` は現状すべてのレコードでNULLとなり、実質的に使用されない状態になった。しかし以下の理由からカラム自体の削除（マイグレーション）は行わない。

- 将来的にグループ固有カテゴリ機能を復活させる可能性に備え、テーブル構造の再利用性を残すため。
- `group_id` を削除するマイグレーションは破壊的変更であり、現時点でのメリットがコストを上回らないため。

### ⑤ 【v1.3で追加】users.display_name のNOT NULL制約について
既存ユーザーが存在する状態でNOT NULL列を追加する場合、Alembicの`--autogenerate`で生成されるリビジョンには、既存行を埋めるための値（`server_default`の一時指定、または事前のUPDATE文）が必要になる可能性がある。マイグレーション実行前に、自動生成されたリビジョンファイルの内容を必ず確認すること。

---

## 1. データベース概要

本システムは、ユーザー、グループ、書類、および通知・リマインドを管理するため、リレーショナルデータベースとして **PostgreSQL** を採用する。

オブジェクトのID（主キー）には、分散環境での競合を避けるため、**全テーブル共通でUUID（v4）** を採用する（`bigint` 等の連番は使用しない）。

---

## 2. テーブル一覧

| 物理テーブル名 | 論理テーブル名 | 概要 |
|---|---|---|
| `users` | ユーザー情報 | アプリ登録者のアカウント情報・プラン状態を管理。**【v1.3】表示名（`display_name`）を追加。** |
| `groups` | 共有グループ情報 | 書類を共有するグループ（家族や個人）を管理。 |
| `group_members` | グループ所属情報 | ユーザーとグループの多対多の紐づけを管理（一律同等権限）。 |
| `invitations` | グループ招待管理 | 他ユーザーをグループに招待するためのステータス管理。 |
| `categories` | カテゴリマスタ | 書類の分類マスタ。固定11種類の共通カテゴリのみで運用（グループ固有カテゴリは提供しない）。 |
| `documents` | 書類情報 | スキャンされた書類のメタデータ、AI解析結果、ステータスを管理。 |
| `app_notifications` | アプリ内お知らせデータ | アプリ内ヘッダー（🔔）に表示する通知ログ。 |
| `notification_schedules` | メールリマインド管理 | Celeryが参照する、期限前メールリマインドの送信キュー。 |

---

## 3. テーブル詳細定義

### 3.1. users（ユーザー情報）【v1.3で変更】

Firebase Authと連携するユーザーの基本情報、プラン状態、共通リマインド設定を一括管理する。**`display_name` / `plan_status` / `monthly_scan_count` / `remind_days_before` はこのテーブルで管理する。**

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| ユーザーID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | 内部管理用PK |
| Firebase UID | `firebase_uid` | VARCHAR(128) | UNIQUE, NOT NULL | - | Firebase Authから発行されるUID |
| メールアドレス | `email` | VARCHAR(255) | UNIQUE, NOT NULL | - | ログイン・リマインド送信先メールアドレス（`notification_schedules.user_id` から参照される） |
| **表示名** | **`display_name`** | **VARCHAR(50)** | **NOT NULL** | **-** | **【新規追加・v1.3】グループメンバー一覧（UI-006-G）等で表示する名前。BE①提案・決定事項としてプッシュ済み。** |
| プランステータス | `plan_status` | VARCHAR(50) | NOT NULL | `'free'` | `'free'` / `'premium'` など |
| 月間スキャン数 | `monthly_scan_count` | INTEGER | NOT NULL | `0` | 毎月1日AM0:00にCelery Beatで0にリセット |
| リマインド設定日数 | `remind_days_before` | INTEGER | NOT NULL | `3` | 期限の何日前に通知するか（デフォルト3日前） |
| 作成日時 | `created_at` | TIMESTAMP | NOT NULL | `CURRENT_TIMESTAMP` | アカウント作成日時 |

> ⚠️ **マイグレーション時の注意（v1.3）**：`display_name`はNOT NULL制約付きのため、既存ユーザー行が存在する状態で`alembic upgrade`を実行するとデフォルト値が無いとエラーになる可能性がある。`--autogenerate`で生成されたリビジョンファイルに、一時的な`server_default`指定または既存行へのUPDATE処理が入っているか確認すること。

### 3.2. groups（共有グループ情報）

書類を共有する器。1人利用時も「個人グループ」として自動生成される。

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| グループID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | グループPK |
| グループ名 | `name` | VARCHAR(100) | NOT NULL | - | 例:「〇〇さんのマイグループ」 |
| 作成者ユーザーID | `created_by` | **UUID** | FOREIGN KEY, NOT NULL | - | `users.id` へ接続。このユーザーのみグループ削除可能 |
| 作成日時 | `created_at` | TIMESTAMP | NOT NULL | `CURRENT_TIMESTAMP` | グループ作成日時 |

### 3.3. group_members（グループ所属情報）

グループとユーザーの中間テーブル。権限（role）の概念はなく、所属者は一律で全操作が可能。

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| 所属ID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | 中間テーブルPK |
| グループID | `group_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `groups.id` へ接続（ON DELETE CASCADE） |
| ユーザーID | `user_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `users.id` へ接続（ON DELETE CASCADE） |
| 参加日時 | `joined_at` | TIMESTAMP | NOT NULL | `CURRENT_TIMESTAMP` | グループに参加した日時 |

> **複合ユニーク制約**：`(group_id, user_id)` の組み合わせは一意とする。

### 3.4. invitations（グループ招待管理）

他のユーザーを共有グループに引き入れるための招待トークン・状態管理。

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| 招待ID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | 招待PK |
| グループID | `group_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `groups.id` へ接続（ON DELETE CASCADE） |
| 招待元ユーザーID | `invited_by` | **UUID** | FOREIGN KEY, NOT NULL | - | `users.id` へ接続 |
| 招待先メールアドレス | `invitee_email` | VARCHAR(255) | NOT NULL | - | 招待を送る対象のメールアドレス |
| ステータス | `status` | VARCHAR(20) | NOT NULL | `'pending'` | `'pending'` / `'accepted'` / `'rejected'` |
| 招待トークン | `token` | VARCHAR(255) | UNIQUE, NOT NULL | - | URL検証用の一意なトークン文字列 |
| 作成日時 | `created_at` | TIMESTAMP | NOT NULL | `CURRENT_TIMESTAMP` | 招待URL発行日時 |
| 有効期限 | `expires_at` | TIMESTAMP | NOT NULL | - | 招待URLの有効期限（24時間後など） |

### 3.5. categories（カテゴリマスタ）

固定11種類の共通カテゴリのみで運用する。グループ固有カテゴリ機能は提供しないため、`group_id` は実質的に常にNULLとなる。

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| カテゴリID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | カテゴリPK |
| グループID | `group_id` | **UUID** | FOREIGN KEY | NULL | `groups.id` へ接続。実質常にNULL（将来のグループ固有カテゴリ復活に備えて列のみ残す） |
| カテゴリ名 | `name` | VARCHAR(50) | NOT NULL | - | 固定11種類のいずれか |
| カラーコード | `color_code` | VARCHAR(7) | - | NULL | カレンダー表示用のカラー（例: `#FF5733`） |
| アイコン | `icon` | VARCHAR(20) | - | NULL | 絵文字を想定（複合的な絵文字（ZWJ結合等）を考慮し余裕を持った文字数で設計） |

> **初期シードデータ（必須）**：`group_id = NULL` とした状態で、以下11レコードをシステム起動時に投入すること。既存行に`icon`が未設定の場合は補完する（idempotent）。「その他」は必ず最後（キャッチオール）に残す。
>
> | name | icon |
> |---|---|
> | 学校 | 🎓 |
> | 医療 | 🏥 |
> | 行政 | 🏛️ |
> | 保険 | 🛡️ |
> | 税金 | 🧾 |
> | 住居・暮らし | 🏠 |
> | 子育て | 👶 |
> | 介護 | 🧑‍🦽 |
> | 仕事 | 💼 |
> | 趣味 | 🎨 |
> | その他 | 📄 |

### 3.6. documents（書類情報）

ユーザーが撮影した書類データ。AIによる解析結果、およびユーザーの修正内容を保持。

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| 書類ID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | 書類PK |
| グループID | `group_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `groups.id` へ接続。書類はグループに帰属する |
| カテゴリID | `category_id` | **UUID** | FOREIGN KEY | NULL | `categories.id` へ接続（NULL許容） |
| タイトル | `title` | VARCHAR(255) | - | NULL | AI抽出または手入力された書類名 |
| 画像URL | `image_url` | TEXT | NOT NULL | - | Cloudinaryに保存された画像の署名付きURL（一時） |
| 期限有無フラグ | `has_deadline` | BOOLEAN | NOT NULL | `false` | 期限があるタスクかどうかの判定 |
| 期限日 | `deadline_date` | DATE | - | NULL | `has_deadline` が true の場合の期日 |
| 済スタンプフラグ | `is_done` | BOOLEAN | NOT NULL | `false` | true の場合、カレンダー上でグレーアウト表現 |
| 登録者ユーザーID | `created_by` | **UUID** | FOREIGN KEY, NOT NULL | - | `users.id` へ接続（撮影・登録した本人） |
| 作成日時 | `created_at` | TIMESTAMP | NOT NULL | `CURRENT_TIMESTAMP` | 書類の登録日時 |

### 3.7. app_notifications（アプリ内お知らせデータ）

誰かが書類を登録した際に、同じグループの他メンバーのベルマーク（🔔）に届く通知ログ。

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| 通知ID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | 通知PK |
| グループID | `group_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `groups.id` へ接続 |
| トリガーユーザーID | `triggered_by` | **UUID** | FOREIGN KEY, NOT NULL | - | `users.id`（書類を登録したユーザー本人） |
| 書類ID | `document_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `documents.id` へ接続（ON DELETE CASCADE） |
| メッセージ本文 | `message` | TEXT | NOT NULL | - | 例：「〇〇さんが書類を登録しました」 |
| 既読フラグ | `is_read` | BOOLEAN | NOT NULL | `false` | 個別タップで true に更新 |
| 作成日時 | `created_at` | TIMESTAMP | NOT NULL | `CURRENT_TIMESTAMP` | 新着順（降順）ソート用の必須カラム |

### 3.8. notification_schedules（メールリマインド管理）

Celery Workerが定期実行時にスキャンするリマインドキュー。**`user_id` が「誰に送るか」を一意に示すカラムであり、メールアドレスは持たない。**

| カラム名（論理） | 物理名 | データ型 | 制約 | 初期値 | 説明 |
|---|---|---|---|---|---|
| タスクID | `id` | **UUID** | PRIMARY KEY | `gen_random_uuid()` | リマインドタスクPK |
| 書類ID | `document_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `documents.id` へ接続（ON DELETE CASCADE） |
| 対象ユーザーID | `user_id` | **UUID** | FOREIGN KEY, NOT NULL | - | `users.id` へ接続。**送信先の特定キー**。Celeryはこの`user_id`から`users.email`を取得して送信する |
| 送信予定日時 | `scheduled_for` | TIMESTAMP | NOT NULL | - | 書類の `deadline_date` から逆算された送信日時 |
| ステータス | `status` | VARCHAR(20) | NOT NULL | `'pending'` | `'pending'` / `'sent'` / `'failed'` / `'cancelled'` |
| リトライ回数 | `retry_count` | INTEGER | NOT NULL | `0` | 外部通信（SendGrid）失敗時にインクリメント（最大3） |
| 作成日時 | `created_at` | TIMESTAMP | NOT NULL | `CURRENT_TIMESTAMP` | タスクの生成日時（ログ・デバッグ用） |

> **ステータス連動ロジック（重要）**：書類（`documents`）の `is_done`（済スタンプ）が `true` に更新された、または書類自体が削除された場合、該当する `document_id` かつ `status = 'pending'` のレコードはバックエンド処理によって即座に `'cancelled'` へ一括更新すること。

---

## 4. 主要なインデックス（パフォーマンス・チューニング）

検索の高速化およびCelery等のバッチ処理最適化のため、以下のインデックス（INDEX）を付与することを推奨する。

| 対象 | 目的 |
|---|---|
| `users(firebase_uid)` | Firebase認証時のユーザー特定を高速化（UNIQUE制約により自動生成）。 |
| `group_members(user_id)` / `group_members(group_id)` | ユーザーの所属グループ一覧、およびグループ内のメンバー一覧の取得高速化。 |
| `documents(group_id, deadline_date)` | カレンダー画面（UI-002）での月間スケジュール高速抽出。 |
| `app_notifications(group_id, created_at DESC)` | 他メンバーのマイページで🔔マークの新着通知をソートして高速表示するため。 |
| `notification_schedules(scheduled_for, status)` | Celery Workerが「送信予定日時を過ぎている ＆ pending 状態」のタスクを毎時（あるいは数分おきに）検索するバッチ処理の負荷を軽減するため。 |
| `notification_schedules(user_id)` | 「済スタンプ」押下時など、特定ユーザー宛のリマインドを検索・更新する際の高速化（補足追加）。 |