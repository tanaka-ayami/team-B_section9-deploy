import { subscribeIdToken } from "./firebase";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

let currentToken: string | null = null;

if (typeof window !== "undefined") {
  subscribeIdToken((token) => { currentToken = token; });
}

type Method = "GET" | "POST" | "PATCH" | "DELETE";

async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
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
  get:      <T>(path: string)                 => request<T>("GET",    path),
  post:     <T>(path: string, body?: unknown) => request<T>("POST",   path, body),
  patch:    <T>(path: string, body?: unknown) => request<T>("PATCH",  path, body),
  delete:   <T>(path: string)                 => request<T>("DELETE", path),
  postForm: <T>(path: string, form: FormData) => requestForm<T>(path, form),
};