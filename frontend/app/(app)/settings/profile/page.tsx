"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { userApi } from "@/lib/api";

export default function ProfileEditPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    userApi.getMe().then((me) => {
      setDisplayName(me.display_name);
      setEmail(me.email);
    });
  }, []);

  const handleSave = async () => {
    if (!displayName.trim()) {
      setError("表示名を入力してください");
      return;
    }
    setError("");
    setIsSaving(true);
    try {
      await userApi.updateMe({ display_name: displayName });
      router.back();
    } catch {
      setError("保存に失敗しました。再度お試しください。");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f2f1ec]">
      {/* ヘッダー */}
      <div className="bg-[#557C79] px-4 pt-12 pb-4 flex items-center gap-3">
        <button
          type="button"
          onClick={() => router.back()}
          className="w-8 h-8 flex items-center justify-center rounded-full"
          style={{ background: "rgba(255,255,255,0.2)" }}
          aria-label="戻る"
        >
          <svg
            className="w-5 h-5 text-white"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 19.5L8.25 12l7.5-7.5"
            />
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-white">プロフィール編集</h1>
      </div>

      <div className="px-4 py-6 space-y-4">
        {/* 表示名入力 */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">表示名</p>
          <div className="bg-white rounded-2xl px-4 py-3 flex items-center gap-3">
            <svg
              className="w-5 h-5 text-[#557C79] flex-shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
              />
            </svg>
            <input
              type="text"
              value={displayName}
              onChange={(e) => {
                setDisplayName(e.target.value);
                setError("");
              }}
              placeholder="お名前（例：山田 太郎）"
              className="flex-1 text-sm text-[#1F2D24] placeholder-[#8fa09e] outline-none bg-transparent"
            />
          </div>
          {error && (
            <p className="text-xs text-[#D45D1E] mt-1.5 px-1">{error}</p>
          )}
        </div>

        {/* メールアドレス（読み取り専用） */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">メールアドレス</p>
          <div className="bg-white rounded-2xl px-4 py-3 flex items-center gap-3">
            <svg
              className="w-5 h-5 text-[#8fa09e] flex-shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75"
              />
            </svg>
            <p className="flex-1 text-sm text-[#8fa09e]">{email}</p>
          </div>
        </div>

        {/* 保存ボタン */}
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="w-full py-3 rounded-2xl text-sm font-semibold text-white flex items-center justify-center gap-2 transition-opacity"
          style={{ backgroundColor: "#557C79", opacity: isSaving ? 0.7 : 1 }}
        >
          {isSaving ? (
            <>
              <svg
                className="w-4 h-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z"
                />
              </svg>
              保存中...
            </>
          ) : (
            "保存する"
          )}
        </button>
      </div>
    </div>
  );
}
