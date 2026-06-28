"use client";

import { useRouter } from "next/navigation";
import { DeadlineBadge } from "./DeadlineBadge";

interface DocumentCardProps {
  id: string;
  title: string;
  categoryName?: string;
  categoryIcon?: string;  // ← この1行を追加
  createdByName?: string;
  deadlineDate?: string;
  hasDeadline: boolean;
  isDone: boolean;
}

export function DocumentCard({
  id,
  title,
  categoryIcon,
  createdByName,
  deadlineDate,
  hasDeadline,
  isDone,
}: DocumentCardProps) {
  const router = useRouter();
  const icon = categoryIcon ?? "📄";

  return (
    <button
      type="button"
      onClick={() => router.push(`/documents/${id}`)}
      className="w-full text-left rounded-2xl px-4 py-3 flex items-center gap-3 mb-2"
      style={{
        backgroundColor: isDone ? "#F3F4F6" : "#ffffff",
        border: "1px solid #C8D4C9",
        opacity: isDone ? 0.7 : 1,
      }}
    >
      {/* カテゴリアイコン */}
      <span
        className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0"
        style={{ backgroundColor: "#EEF1EC" }}
      >
        {icon}
      </span>

      {/* テキスト */}
      <div className="flex-1 min-w-0">
        <p
          className="text-sm font-medium truncate"
          style={{ color: isDone ? "#9CA3AF" : "#1F2D24" }}
        >
          {title}
        </p>
        <p className="text-xs mt-0.5" style={{ color: "#6B7C6F" }}>
          {[createdByName, deadlineDate].filter(Boolean).join("・")}
        </p>
      </div>

      {/* バッジ */}
      {hasDeadline && deadlineDate && (
        <DeadlineBadge deadlineDate={deadlineDate} isDone={isDone} />
      )}
    </button>
  );
}