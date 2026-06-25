// frontend/app/(app)/documents/[id]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import dayjs from "dayjs";
import { apiClient } from "@/lib/api";
import { Document, PatchDocumentRequest } from "@/types/document";

// ─── モックデータ（Week2でAPIに切り替え） ───────────────────────
const MOCK_DOCUMENT: Document = {
  id: "doc-001",
  title: "夏期講習 申込書",
  category_id: "cat-001",
  categoryName: "学校",
  group_id: "group-001",
  image_url: "",
  has_deadline: true,
  deadline_date: "2026-06-26",
  is_done: false,
  created_by: "user-001",
  created_at: "2026-06-20T10:00:00Z",
};
// ────────────────────────────────────────────────────────────────

export default function DocumentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [doc, setDoc] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDone, setIsDone] = useState(false);
  const [reminderCancelled, setReminderCancelled] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // トースト表示
  function showToast(message: string) {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  }

  // 書類取得（現在はモック）
  useEffect(() => {
    setLoading(true);
    // TODO: Week2で apiClient.get<Document>(`/v1/documents/${id}`) に切り替え
    setTimeout(() => {
      setDoc(MOCK_DOCUMENT);
      setIsDone(MOCK_DOCUMENT.is_done);
      setLoading(false);
    }, 300);
  }, [id]);

  // 済スタンプ切り替え
  async function handleToggleDone() {
    if (!doc) return;
    const newIsDone = !isDone;
    setIsDone(newIsDone);
    try {
      // TODO: Week2で実API接続
      // await apiClient.patch<Document>(`/v1/documents/${id}`, { is_done: newIsDone });
      if (newIsDone) {
        setReminderCancelled(true);
        showToast("リマインドメールがキャンセルされました");
      } else {
        setReminderCancelled(false);
      }
    } catch {
      setIsDone(!newIsDone); // ロールバック
      showToast("更新に失敗しました");
    }
  }

  // 削除
  async function handleDelete() {
    try {
      // TODO: Week2で実API接続
      // await apiClient.delete(`/v1/documents/${id}`);
      showToast("書類を削除しました");
      setTimeout(() => router.replace("/calendar"), 1000);
    } catch {
      showToast("削除に失敗しました");
    }
    setShowDeleteDialog(false);
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec]">
        <svg className="w-8 h-8 animate-spin text-[#557C79]" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z" />
        </svg>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec]">
        <p className="text-sm text-[#6B7C6F]">書類が見つかりません</p>
      </div>
    );
  }

  const formattedDeadline = doc.deadline_date
    ? dayjs(doc.deadline_date).format("YYYY年M月D日（ddd）")
    : null;

  const reminderDate = doc.deadline_date
    ? dayjs(doc.deadline_date).subtract(3, "day").format("M月D日（ddd）")
    : null;

  return (
    <div className="min-h-screen bg-[#f2f1ec]">
      {/* トースト */}
      {toast && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-[#1F2D24] text-white text-sm px-4 py-2 rounded-full shadow-lg">
          {toast}
        </div>
      )}

      {/* ヘッダー */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ backgroundColor: "#557C79" }}
      >
        <button
          type="button"
          onClick={() => router.back()}
          className="text-white p-1"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span className="text-white font-medium text-sm">書類の詳細</span>
        <button
          type="button"
          className="text-white text-xs border border-white/50 rounded-full px-3 py-1"
          onClick={() => showToast("再編集は Week2 で実装予定です")}
        >
          ✏ 再編集
        </button>
      </div>

      <div className="px-4 pt-4 pb-32 space-y-3">
        {/* 書類画像 */}
        <div
          className="w-full h-48 rounded-2xl flex items-center justify-center"
          style={{ backgroundColor: "#E8EDEA" }}
        >
          {doc.image_url ? (
            <img src={doc.image_url} alt={doc.title ?? ""} className="w-full h-full object-contain rounded-2xl" />
          ) : (
            <svg className="w-12 h-12 text-[#9DB4A8]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          )}
        </div>

        {/* 書類情報カード */}
        <div className="bg-white rounded-2xl overflow-hidden" style={{ border: "1px solid #C8D4C9" }}>
          {/* タイトル */}
          <div className="px-4 py-3 flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1">
              <span className="text-base mt-0.5">🏷</span>
              <div>
                <p className="text-xs text-[#6B7C6F] mb-0.5">書類タイトル</p>
                <p className="text-sm font-medium text-[#1F2D24]">{doc.title ?? "タイトルなし"}</p>
              </div>
            </div>
            {doc.categoryName && (
              <span
                className="text-xs px-2 py-0.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: "#EEF1EC", color: "#4A7C59" }}
              >
                {doc.categoryName}
              </span>
            )}
          </div>

          <div style={{ borderTop: "1px solid #EEF1EC" }} />

          {/* 提出期限 */}
          <div className="px-4 py-3 flex items-start gap-2">
            <span className="text-base mt-0.5">📅</span>
            <div>
              <p className="text-xs text-[#6B7C6F] mb-0.5">提出期限</p>
              <p className="text-sm font-medium text-[#1F2D24]">
                {doc.has_deadline && formattedDeadline ? formattedDeadline : "期限なし"}
              </p>
            </div>
          </div>

          <div style={{ borderTop: "1px solid #EEF1EC" }} />

          {/* カテゴリ */}
          <div className="px-4 py-3 flex items-start gap-2">
            <span className="text-base mt-0.5">📂</span>
            <div>
              <p className="text-xs text-[#6B7C6F] mb-0.5">カテゴリ</p>
              <p className="text-sm font-medium text-[#1F2D24]">{doc.categoryName ?? "未分類"}</p>
            </div>
          </div>
        </div>

        {/* 済スタンプカード */}
        <div className="bg-white rounded-2xl px-4 py-3" style={{ border: "1px solid #C8D4C9" }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-base">✅</span>
              <span className="text-sm font-medium text-[#1F2D24]">済スタンプ</span>
            </div>
            {/* トグル */}
            <button
              type="button"
              onClick={handleToggleDone}
              className="relative w-12 h-6 rounded-full transition-colors duration-200 flex-shrink-0"
              style={{ backgroundColor: isDone ? "#557C79" : "#D1D5DB" }}
            >
              <span
                className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                style={{ transform: isDone ? "translateX(24px)" : "translateX(2px)" }}
              />
            </button>
          </div>
          <p className="text-xs text-[#6B7C6F] mt-2 leading-relaxed">
            完了したらONに。ONにすると未送信のリマインドメールが自動キャンセルされます。
          </p>
        </div>

        {/* リマインドメールカード */}
        {doc.has_deadline && (
          <div className="bg-white rounded-2xl px-4 py-3" style={{ border: "1px solid #C8D4C9" }}>
            <div className="flex items-start gap-2">
              <span className="text-base mt-0.5">✉</span>
              <div>
                <p className="text-xs text-[#6B7C6F] mb-0.5">リマインドメール</p>
                {reminderCancelled || isDone ? (
                  <p className="text-sm text-[#9CA3AF]">キャンセルされました</p>
                ) : (
                  <p className="text-sm text-[#1F2D24]">
                    {reminderDate} に送信予定
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 削除ボタン */}
        <button
          type="button"
          onClick={() => setShowDeleteDialog(true)}
          className="w-full py-3 rounded-2xl text-sm font-medium flex items-center justify-center gap-2"
          style={{ backgroundColor: "#FEE2E2", color: "#DC2626", border: "1px solid #FECACA" }}
        >
          🗑 この書類を削除
        </button>
      </div>

      {/* 削除確認ダイアログ */}
      {showDeleteDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl mx-6 p-6 shadow-xl">
            <p className="text-sm font-medium text-[#1F2D24] mb-1">この書類を削除しますか？</p>
            <p className="text-xs text-[#6B7C6F] mb-5">削除すると元に戻せません。</p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setShowDeleteDialog(false)}
                className="flex-1 py-2 rounded-xl text-sm text-[#6B7C6F]"
                style={{ backgroundColor: "#F3F4F6" }}
              >
                キャンセル
              </button>
              <button
                type="button"
                onClick={handleDelete}
                className="flex-1 py-2 rounded-xl text-sm font-medium text-white"
                style={{ backgroundColor: "#DC2626" }}
              >
                削除する
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}