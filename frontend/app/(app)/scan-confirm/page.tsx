"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface AiAnalysis {
  title: string | null;
  category: string | null;
  deadline: string | null;
  has_deadline: boolean;
}

interface ScanResult {
  image_url: string | null;
  ai_analysis: AiAnalysis | null;
}

const CATEGORIES = ["学校", "医療", "行政", "保険", "その他"];

export default function ScanConfirmPage() {
  const router = useRouter();
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [hasDeadline, setHasDeadline] = useState(false);
  const [deadlineDate, setDeadlineDate] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAnalyzed = scanResult?.ai_analysis !== null;

  useEffect(() => {
    const raw = sessionStorage.getItem("scanResult");
    if (!raw) { router.replace("/scan"); return; }
    const result: ScanResult = JSON.parse(raw);
    setScanResult(result);
    if (result.ai_analysis) {
      setTitle(result.ai_analysis.title ?? "");
      setCategory(result.ai_analysis.category ?? null);
      setHasDeadline(result.ai_analysis.has_deadline);
      setDeadlineDate(result.ai_analysis.deadline ?? "");
    }
  }, [router]);

  const handleSubmit = async () => {
    if (!title.trim()) return;
    setIsSubmitting(true);
    try {
      // TODO Week2: POST /v1/documents
      console.log("登録データ:", { title, category, hasDeadline, deadlineDate });
      sessionStorage.removeItem("scanResult");
      router.replace("/calendar");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!scanResult) return null;

  return (
    <div className="min-h-screen pb-8 bg-[#f2f1ec]">
      {/* ヘッダー */}
      <div className="flex items-center px-4 pt-12 pb-4 bg-[#557C79]">
        <button
          type="button"
          onClick={() => router.back()}
          className="w-9 h-9 rounded-full flex items-center justify-center mr-3"
          style={{ background: "rgba(255,255,255,0.2)" }}
        >
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5"/>
          </svg>
        </button>
        <h1 className="text-white text-base font-medium">解析結果の確認・編集</h1>
      </div>

      <div className="px-4 pt-4 space-y-4">
        {/* 画像プレビュー */}
        {scanResult.image_url && (
          <div className="relative rounded-2xl overflow-hidden bg-white border border-[#D2D4BC]">
            <img src={scanResult.image_url} alt="書類" className="w-full object-contain max-h-48"/>
            <span
              className="absolute top-2 right-2 text-xs px-2 py-1 rounded-full font-medium"
              style={isAnalyzed
                ? { backgroundColor: "#f2f1ec", color: "#557C79" }
                : { backgroundColor: "#FCEBEB", color: "#E24B4A" }}
            >
              {isAnalyzed ? "✦ AI解析済み" : "⚠ 解析失敗"}
            </span>
          </div>
        )}

        {/* エラーバナー */}
        {!isAnalyzed && (
          <div className="rounded-2xl px-4 py-3 text-sm"
            style={{ backgroundColor: "#FCEBEB", color: "#E24B4A" }}>
            ⚠ 解析ができませんでした。手動での入力をお願いします
          </div>
        )}

        {/* 書類タイトル */}
        <div>
          <p className="text-xs font-medium mb-1.5 text-[#557C79] opacity-70">書類タイトル</p>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="タイトルを入力してください"
            className="w-full rounded-2xl px-4 py-3 text-sm outline-none bg-white text-[#1F2D24]"
            style={{
              border: `1px solid ${!title.trim() ? "#E24B4A" : "#D2D4BC"}`,
            }}
          />
        </div>

        {/* カテゴリ */}
        <div>
          <p className="text-xs font-medium mb-1.5 text-[#557C79] opacity-70">カテゴリ</p>
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat === category ? null : cat)}
                className="px-3 py-1.5 rounded-full text-sm transition-colors"
                style={category === cat
                  ? { backgroundColor: "#557C79", color: "#fff" }
                  : { backgroundColor: "#fff", color: "#557C79", border: "1px solid #D2D4BC" }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* 期限の有無 */}
        <div className="rounded-2xl px-4 py-3 flex items-center justify-between bg-white border border-[#D2D4BC]">
          <p className="text-sm text-[#1F2D24]">
            {hasDeadline ? "期限あり" : "期限なし"}
          </p>
          <button
            type="button"
            onClick={() => setHasDeadline((v) => !v)}
            className="w-11 h-6 rounded-full transition-colors relative"
            style={{ backgroundColor: hasDeadline ? "#557C79" : "#D2D4BC" }}
          >
            <span
              className="absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform"
              style={{ transform: hasDeadline ? "translateX(22px)" : "translateX(2px)" }}
            />
          </button>
        </div>

        {/* 提出期限 */}
        {hasDeadline && (
          <div>
            <p className="text-xs font-medium mb-1.5 text-[#557C79] opacity-70">提出期限</p>
            <input
              type="date"
              value={deadlineDate}
              onChange={(e) => setDeadlineDate(e.target.value)}
              className="w-full rounded-2xl px-4 py-3 text-sm outline-none bg-white border border-[#D2D4BC] text-[#1F2D24]"
            />
          </div>
        )}

        {/* 登録ボタン */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!title.trim() || isSubmitting}
          className="w-full rounded-2xl py-4 text-sm font-medium text-white transition-colors"
          style={{ backgroundColor: !title.trim() ? "#D2D4BC" : "#557C79" }}
        >
          {isSubmitting ? "登録中..." : isAnalyzed ? "✓ この内容で登録する" : "✓ 手入力で登録する"}
        </button>

        <p className="text-xs text-center text-[#8fa09e]">
          登録後も詳細画面から再修正できます
        </p>
      </div>
    </div>
  );
}