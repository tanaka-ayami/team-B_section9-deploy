"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { groupApi } from "@/lib/api";

export default function NewGroupPage() {
  const router = useRouter();
  const [groupName, setGroupName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmedName = groupName.trim();
  const isValid = trimmedName.length > 0;

  const handleCreate = async () => {
    if (!isValid || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const created = await groupApi.create(trimmedName);
      router.replace(`/settings/groups/${created.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "グループの作成に失敗しました");
      setIsSubmitting(false);
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
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-white">新しいグループを作成</h1>
      </div>

      <div className="px-4 py-4 space-y-4 pb-8">
        <div className="bg-white rounded-2xl p-4 space-y-3">
          <label className="block">
            <span className="text-xs text-[#8fa09e] mb-1.5 block">グループ名</span>
            <input
              type="text"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              placeholder="例：山田ファミリー"
              autoFocus
              className="w-full px-4 py-3 rounded-xl border border-[#D2D4BC] bg-[#F5F6F2] text-sm text-[#1F2D24] placeholder-[#8fa09e] outline-none"
            />
          </label>

          {error && (
            <p className="text-xs text-[#E24B4A]">{error}</p>
          )}
        </div>

        <button
          type="button"
          onClick={handleCreate}
          disabled={!isValid || isSubmitting}
          className="w-full py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-60"
          style={{ backgroundColor: "#557C79" }}
        >
          {isSubmitting ? "作成中..." : "作成する"}
        </button>
      </div>
    </div>
  );
}