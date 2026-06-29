"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { categoryApi, groupApi, documentApi, Category, Group } from "@/lib/api";

interface ScanResult {
  image_url: string | null;
  title: string | null;
  category: string | null;
  deadline: string | null;
  has_deadline: boolean;
}

export default function ScanConfirmPage() {
  const router = useRouter();
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [title, setTitle] = useState("");

  // カテゴリ：名前文字列ではなくidで管理（APIから取得した11種類）
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [aiCategoryName, setAiCategoryName] = useState<string | null>(null);

  // 登録先グループ（自分が所属するグループから選択。デフォルトは最初の1件）
  const [groups, setGroups] = useState<Group[]>([]);
  const [groupId, setGroupId] = useState<string | null>(null);

  const [hasDeadline, setHasDeadline] = useState(false);
  const [deadlineDate, setDeadlineDate] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // 解析できたかどうかは title が取れているかで判定する
  // （バックエンドのレスポンスはネストせずフラットな形で返ってくる）
  const isAnalyzed = !!scanResult?.title;

  // スキャン結果の読み込み
  useEffect(() => {
    const raw = sessionStorage.getItem("scanResult");
    if (!raw) {
      router.replace("/scan");
      return;
    }
    const result: ScanResult = JSON.parse(raw);
    setScanResult(result);
    if (result.title) {
      setTitle(result.title ?? "");
      setAiCategoryName(result.category ?? null);
      setHasDeadline(result.has_deadline);
      setDeadlineDate(result.deadline ?? "");
    }
  }, [router]);

  // カテゴリ一覧・グループ一覧をAPIから取得
  useEffect(() => {
    categoryApi
      .list()
      .then(setCategories)
      .catch(() => setCategories([]));
    groupApi
      .list()
      .then((gs) => {
        setGroups(gs);
        if (gs.length > 0) setGroupId(gs[0].id); // 最初のグループを自動選択（変更は手動で可能）
      })
      .catch(() => setGroups([]));
  }, []);

  // AIが判定したカテゴリ名 → カテゴリ一覧が揃ってからidに変換して自動選択
  useEffect(() => {
    if (aiCategoryName && categories.length > 0 && !categoryId) {
      const matched = categories.find((c) => c.name === aiCategoryName);
      if (matched) setCategoryId(matched.id);
    }
  }, [aiCategoryName, categories, categoryId]);

  const handleSubmit = async () => {
    if (!title.trim() || !groupId || !scanResult?.image_url) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await documentApi.create({
        group_id: groupId,
        category_id: categoryId,
        title,
        image_url: scanResult.image_url,
        has_deadline: hasDeadline,
        deadline_date: hasDeadline ? deadlineDate : null,
      });
      sessionStorage.removeItem("scanResult");
      router.replace("/calendar");
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : "登録に失敗しました");
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
          <svg
            className="w-5 h-5 text-white"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 19.5 8.25 12l7.5-7.5"
            />
          </svg>
        </button>
        <h1 className="text-white text-base font-medium">
          解析結果の確認・編集
        </h1>
      </div>

      <div className="px-4 pt-4 space-y-4">
        {/* 画像プレビュー */}
        {scanResult.image_url && (
          <div className="relative rounded-2xl overflow-hidden bg-white border border-[#D2D4BC]">
            <img
              src={scanResult.image_url}
              alt="書類"
              className="w-full object-contain max-h-48"
            />
            <span
              className="absolute top-2 right-2 text-xs px-2 py-1 rounded-full font-medium"
              style={
                isAnalyzed
                  ? { backgroundColor: "#f2f1ec", color: "#557C79" }
                  : { backgroundColor: "#FCEBEB", color: "#E24B4A" }
              }
            >
              {isAnalyzed ? "✦ AI解析済み" : "⚠ 解析失敗"}
            </span>
          </div>
        )}

        {/* エラーバナー */}
        {!isAnalyzed && (
          <div
            className="rounded-2xl px-4 py-3 text-sm"
            style={{ backgroundColor: "#FCEBEB", color: "#E24B4A" }}
          >
            ⚠ 解析ができませんでした。手動での入力をお願いします
          </div>
        )}

        {/* 書類タイトル */}
        <div>
          <p className="text-xs font-medium mb-1.5 text-[#557C79] opacity-70">
            書類タイトル
          </p>
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

        {/* カテゴリ（APIから取得した11種類） */}
        <div>
          <p className="text-xs font-medium mb-1.5 text-[#557C79] opacity-70">
            カテゴリ
          </p>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() =>
                  setCategoryId(cat.id === categoryId ? null : cat.id)
                }
                className="px-3 py-1.5 rounded-full text-sm transition-colors"
                style={
                  categoryId === cat.id
                    ? { backgroundColor: "#557C79", color: "#fff" }
                    : {
                        backgroundColor: "#fff",
                        color: "#557C79",
                        border: "1px solid #D2D4BC",
                      }
                }
              >
                {cat.icon ? `${cat.icon} ` : ""}
                {cat.name}
              </button>
            ))}
          </div>
        </div>

        {/* 登録先グループ */}
        <div>
          <p className="text-xs font-medium mb-1.5 text-[#557C79] opacity-70">
            登録先グループ
          </p>
          <div className="flex flex-wrap gap-2">
            {groups.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => setGroupId(g.id)}
                className="px-3 py-1.5 rounded-full text-sm transition-colors"
                style={
                  groupId === g.id
                    ? { backgroundColor: "#557C79", color: "#fff" }
                    : {
                        backgroundColor: "#fff",
                        color: "#557C79",
                        border: "1px solid #D2D4BC",
                      }
                }
              >
                {g.name}
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
              style={{
                transform: hasDeadline ? "translateX(22px)" : "translateX(2px)",
              }}
            />
          </button>
        </div>

        {/* 提出期限 */}
        {hasDeadline && (
          <div>
            <p className="text-xs font-medium mb-1.5 text-[#557C79] opacity-70">
              提出期限
            </p>
            <input
              type="date"
              value={deadlineDate}
              onChange={(e) => setDeadlineDate(e.target.value)}
              className="w-full rounded-2xl px-4 py-3 text-sm outline-none bg-white border border-[#D2D4BC] text-[#1F2D24]"
            />
          </div>
        )}

        {submitError && (
          <div
            className="rounded-2xl px-4 py-3 text-sm"
            style={{ backgroundColor: "#FCEBEB", color: "#E24B4A" }}
          >
            {submitError}
          </div>
        )}

        {/* 登録ボタン */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!title.trim() || !groupId || isSubmitting}
          className="w-full rounded-2xl py-4 text-sm font-medium text-white transition-colors"
          style={{
            backgroundColor: !title.trim() || !groupId ? "#D2D4BC" : "#557C79",
          }}
        >
          {isSubmitting
            ? "登録中..."
            : isAnalyzed
              ? "✓ この内容で登録する"
              : "✓ 手入力で登録する"}
        </button>

        <p className="text-xs text-center text-[#8fa09e]">
          登録後も詳細画面から再修正できます
        </p>
      </div>
    </div>
  );
}
