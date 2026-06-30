import { subscribeIdToken } from "./firebase";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

let currentToken: string | null = null;

if (typeof window !== "undefined") {
  subscribeIdToken((token) => {
    currentToken = token;
  });
}

type Method = "GET" | "POST" | "PATCH" | "DELETE";

async function request<T>(
  method: Method,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (currentToken) headers["Authorization"] = `Bearer ${currentToken}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }

  const text = await res.text();
  return text ? (JSON.parse(text) as T) : ({} as T);
}

async function requestForm<T>(path: string, formData: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  if (currentToken) headers["Authorization"] = `Bearer ${currentToken}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }

  const text = await res.text();
  return text ? (JSON.parse(text) as T) : ({} as T);
}

export const apiClient = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
  postForm: <T>(path: string, form: FormData) => requestForm<T>(path, form),
};

// ===== 型定義 =====

export interface Document {
  id: string;
  group_id: string;
  category_id: string | null;
  categoryName: string | null; // バックエンドが解決済みで返してくれる
  title: string | null;
  image_url: string;
  has_deadline: boolean;
  deadline_date: string | null;
  is_done: boolean;
  created_by: string;
  created_at: string;
}

export interface AppNotification {
  id: string;
  group_id: string;
  triggered_by: string;
  document_id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface Category {
  id: string;
  group_id: string | null;
  name: string;
  color_code: string | null;
  icon: string | null;
}

export interface Group {
  id: string;
  name: string;
  created_by: string;
}

export interface GroupMember {
  id: string;
  group_id: string;
  user_id: string;
  email: string;
  display_name: string;
  joined_at: string;
}

export interface Invitation {
  id: string;
  group_id: string;
  invited_by: string;
  invitee_email: string;
  status: "pending" | "accepted" | "rejected";
  created_at: string;
  expires_at: string;
}

export interface UserMe {
  id: string;
  firebase_uid: string;
  email: string;
  display_name: string;
  plan_status: string;
  monthly_scan_count: number;
  remind_days_before: number;
  email_notify_enabled: boolean;
}

// バックエンドの DocumentCreate スキーマ（documents.py）に合わせた登録用の型
// ※ created_by はトークンから自動設定、is_done はバックエンドが受け取らないため除外
export interface DocumentCreateInput {
  group_id: string;
  category_id?: string | null;
  title?: string | null;
  image_url: string;
  has_deadline?: boolean;
  deadline_date?: string | null;
}

// ===== ユーザー =====

export const userApi = {
  // GET /v1/users/me
  getMe: () => apiClient.get<UserMe>("/v1/users/me"),
  // PATCH /v1/users/me
  updateMe: (
    body: Partial<
      Pick<
        UserMe,
        "display_name" | "remind_days_before" | "email_notify_enabled"
      >
    >,
  ) => apiClient.patch<UserMe>("/v1/users/me", body),
};

// ===== 書類 =====

export const documentApi = {
  // GET /v1/groups/{group_id}/documents（バックエンドの実際のパスに合わせて修正）
  list: (groupId: string) =>
    apiClient
      .get<{ documents: Document[] }>(`/v1/groups/${groupId}/documents`)
      .then((res) => res.documents),
  // GET /v1/documents/:id
  get: (id: string) => apiClient.get<Document>("/v1/documents/" + id),
  // POST /v1/documents
  create: (body: DocumentCreateInput) =>
    apiClient.post<Document>("/v1/documents", body),
  // PATCH /v1/documents/:id
  update: (id: string, body: Partial<Document>) =>
    apiClient.patch<Document>("/v1/documents/" + id, body),
  // DELETE /v1/documents/:id
  delete: (id: string) => apiClient.delete<void>("/v1/documents/" + id),
  // POST /v1/documents/scan
  scan: (formData: FormData) =>
    apiClient.postForm<{
      title: string;
      category: string | null;
      deadline: string | null;
      has_deadline: boolean;
      image_url: string;
    }>("/v1/documents/scan", formData),
};

// ===== 通知 =====

export const notificationApi = {
  // GET /v1/notifications
  list: () => apiClient.get<AppNotification[]>("/v1/notifications"),
  // PATCH /v1/notifications/:id/read
  markRead: (id: string) =>
    apiClient.patch<void>("/v1/notifications/" + id + "/read"),
};

// ===== カテゴリ =====

export const categoryApi = {
  // GET /v1/categories
  list: () => apiClient.get<Category[]>("/v1/categories"),
};

// ===== グループ =====

export const groupApi = {
  // GET /v1/groups
  list: () => apiClient.get<Group[]>("/v1/groups"),
  // POST /v1/groups
  create: (name: string) => apiClient.post<Group>("/v1/groups", { name }),
  // DELETE /v1/groups/:id
  delete: (id: string) => apiClient.delete<void>("/v1/groups/" + id),
  // PATCH /v1/groups/:id
  update: (id: string, name: string) =>
    apiClient.patch<Group>("/v1/groups/" + id, { name }),
  // GET /v1/groups/:id/members
  getMembers: (id: string) =>
    apiClient.get<GroupMember[]>("/v1/groups/" + id + "/members"),
  // POST /v1/groups/:id/invite
  invite: (id: string, email: string) =>
    apiClient.post<Invitation>("/v1/groups/" + id + "/invite", {
      invitee_email: email,
    }),
  // GET /v1/groups/:id/invitations
  getInvitations: (id: string) =>
    apiClient.get<Invitation[]>("/v1/groups/" + id + "/invitations"),
};

// ===== 招待（招待された側） =====

export interface InvitationPublic {
  group_name: string;
  invited_by_email: string;
  status: string;
  expires_at: string;
}

export const invitationApi = {
  // GET /v1/invitations/:token（認証不要）
  get: (token: string) =>
    apiClient.get<InvitationPublic>("/v1/invitations/" + token),
  // POST /v1/invitations/:token/accept
  accept: (token: string) =>
    apiClient.post<{ group_id: string; status: string; message: string }>(
      "/v1/invitations/" + token + "/accept",
    ),
  // POST /v1/invitations/:token/reject
  reject: (token: string) =>
    apiClient.post<{ status: string }>("/v1/invitations/" + token + "/reject"),
};

// ===== 課金 =====

export const billingApi = {
  // POST /v1/billing/checkout-session
  createCheckoutSession: () =>
    apiClient.post<{ checkout_url: string }>("/v1/billing/checkout-session"),
};
