// frontend/app/(app)/documents/[id]/edit/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { documentApi, categoryApi, Document, Category } from "@/lib/api";

export default function DocumentEditPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [doc, setDoc] = useState<Document | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [hasDeadline, setHasDeadline] = useState(false);
  const [deadlineDate, setDeadlineDate] = useState("");

  function showToast(message: string) {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  }

  useEffect(() => {
    setLoading(true);
    Promise.all([documentApi.get(id), categoryApi.list()])
      .then(([docData, categoryData]) => {
        setDoc(docData);
        setCategories(categoryData);
        setTitle(docData.title ?? "");
        setCategoryId(docData.category_id ?? null);
        setHasDeadline(docData.has_deadline);
        setDeadlineDate(docData.deadline_date ?? "");
      })
      .catch(() => showToast("書類の取得に失敗しました"))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleSave() {
    if (!title.trim()) {
      showToast("タイトルを入力してください");
      return;
    }
    if (hasDeadline && !deadlineDate) {
      showToast("提出期限を選択してください");
      return;
    }
    setSaving(true);
    try {
      await documentApi.update(id, {
        title: title.trim(),
        category_id: categoryId,
        has_deadline: hasDeadline,
        deadline_date: hasDeadline ? deadlineDate : null,
      });
      router.push(`/documents/${id}`);
    } catch {
      showToast("保存に失敗しました");
    } finally {
      setSaving(false);
    }
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

  return (
    <div className="min-h-screen bg-[#f2f1ec]">
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
        <span className="text-white font-medium text-sm">書類を編集</span>
        <span className="w-6" />
      </div>

      <div className="px-4 pt-4 pb-32 space-y-5">
        {/* 書類タイトル */}
        <div>
          <p className="text-xs text-[#6B7C6F] mb-1.5">書類タイトル</p>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="タイトルを入力してください"
            className="w-full px-3 py-2.5 rounded-xl text-sm text-[#1F2D24] bg-white"
            style={{ border: "1px solid #C8D4C9" }}
          />
        </div>

        {/* カテゴリ */}
        <div>
          <p className="text-xs text-[#6B7C6F] mb-1.5">カテゴリ</p>
          <div className="flex flex-wrap gap-2">
            {categories.map((c) => {
              const active = categoryId === c.id;
              return (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setCategoryId(c.id)}
                  className="px-3 py-1.5 rounded-full text-xs font-medium transition-colors"
                  style={{
                    backgroundColor: active ? "#557C79" : "#EEF1EC",
                    color: active ? "#ffffff" : "#4A7C59",
                  }}
                >
                  {c.icon ? `${c.icon} ` : ""}{c.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* 期限の有無 */}
        <div className="bg-white rounded-2xl px-4 py-3 flex items-center justify-between" style={{ border: "1px solid #C8D4C9" }}>
          <span className="text-sm font-medium text-[#1F2D24]">
            {hasDeadline ? "期限あり" : "期限なし"}
          </span>
          <button
            type="button"
            onClick={() => setHasDeadline((v) => !v)}
            className="relative w-12 h-6 rounded-full transition-colors duration-200 flex-shrink-0"
            style={{ backgroundColor: hasDeadline ? "#557C79" : "#D1D5DB" }}
          >
            <span
              className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
              style={{ left: hasDeadline ? "calc(100% - 22px)" : "2px" }}
            />
          </button>
        </div>

        {/* 提出期限 */}
        {hasDeadline && (
          <div>
            <p className="text-xs text-[#6B7C6F] mb-1.5">提出期限</p>
            <input
              type="date"
              value={deadlineDate}
              onChange={(e) => setDeadlineDate(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl text-sm text-[#1F2D24] bg-white"
              style={{ border: "1px solid #C8D4C9" }}
            />
          </div>
        )}

        {/* 保存ボタン */}
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="w-full py-3 rounded-2xl text-sm font-medium text-white disabled:opacity-60"
          style={{ backgroundColor: "#557C79" }}
        >
          {saving ? "保存中..." : "保存する"}
        </button>
      </div>
    </div>
  );
}