"use client";

import { useEffect, useMemo, useState } from "react";
import { DocumentCard } from "@/components/calendar/DocumentCard";
import { groupApi, documentApi, categoryApi, Document, Category } from "@/lib/api";

interface DisplayDocument {
  id: string;
  title: string;
  categoryName?: string;
  categoryIcon?: string;
  deadlineDate?: string;
  hasDeadline: boolean;
  isDone: boolean;
}

const CATEGORY_PILLS = [
  { label: "すべて", value: "all" },
  { label: "学校", value: "学校" },
  { label: "仕事", value: "仕事" },
  { label: "医療", value: "医療" },
  { label: "行政", value: "行政" },
  { label: "保険", value: "保険" },
  { label: "税金", value: "税金" },
  { label: "住居", value: "住居・暮らし" },
  { label: "子育て", value: "子育て" },
  { label: "介護", value: "介護" },
  { label: "趣味", value: "趣味" },
  { label: "その他", value: "その他" },
  { label: "期限なし", value: "no-deadline" },
];

export default function DocumentsPage() {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [documents, setDocuments] = useState<DisplayDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setHasError(false);
      try {
        const [groups, categories] = await Promise.all([
          groupApi.list(),
          categoryApi.list(),
        ]);

        const categoryIconById = new Map<string, string>(
          categories.map((c: Category) => [c.id, c.icon ?? "📄"])
        );

        // 所属する全グループの書類一覧をまとめて取得し合算する
        // （カレンダー画面 UI-002 と同じ取得パターン）
        const docsByGroup = await Promise.all(
          groups.map((g) => documentApi.list(g.id))
        );

        const allDocs: DisplayDocument[] = docsByGroup.flat().map((d: Document) => ({
          id: d.id,
          title: d.title ?? "(無題)",
          categoryName: d.categoryName ?? undefined,
          categoryIcon: d.category_id ? categoryIconById.get(d.category_id) : undefined,
          deadlineDate: d.deadline_date ?? undefined,
          hasDeadline: d.has_deadline,
          isDone: d.is_done,
        }));

        if (!cancelled) setDocuments(allDocs);
      } catch (e) {
        if (!cancelled) {
          setDocuments([]);
          setHasError(true);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (selectedCategory === "all") return documents;
    if (selectedCategory === "no-deadline") {
      return documents.filter((d) => !d.hasDeadline);
    }
    return documents.filter((d) => d.categoryName === selectedCategory);
  }, [documents, selectedCategory]);

  const withDeadline = filtered.filter((d) => d.hasDeadline && !d.isDone);
  const noDeadline = filtered.filter((d) => !d.hasDeadline && !d.isDone);
  const done = filtered.filter((d) => d.isDone);

  return (
    <div className="min-h-screen bg-[#f2f1ec]">
      {/* カテゴリ絞り込みpill */}
      <div className="bg-white border-b border-[#D2D4BC] px-4 py-3">
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {CATEGORY_PILLS.map((pill) => {
            const active = selectedCategory === pill.value;
            return (
              <button
                key={pill.value}
                type="button"
                onClick={() => setSelectedCategory(pill.value)}
                className="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors"
                style={{
                  backgroundColor: active ? "#557C79" : "#f2f1ec",
                  color: active ? "#ffffff" : "#557C79",
                }}
              >
                {pill.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="px-4 pt-4 pb-8">
        {isLoading ? (
          <div className="space-y-3 pt-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-16 rounded-2xl animate-pulse"
                style={{ backgroundColor: "#e5e7eb" }}
              />
            ))}
          </div>
        ) : hasError ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-[#8fa09e]">
            <p className="text-sm">書類の取得に失敗しました</p>
          </div>
        ) : (
          <>
            {/* 件数 */}
            <p className="text-xs text-[#8fa09e] mb-4">{filtered.length}件</p>

            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3 text-[#8fa09e]">
                <svg
                  className="w-12 h-12 opacity-40"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                  />
                </svg>
                <p className="text-sm">書類がありません</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* 期限あり */}
                {withDeadline.length > 0 && (
                  <section>
                    <p className="text-xs text-[#8fa09e] mb-2">期限あり</p>
                    {withDeadline.map((doc) => (
                      <DocumentCard key={doc.id} {...doc} />
                    ))}
                  </section>
                )}

                {/* 期限なし・保管 */}
                {noDeadline.length > 0 && (
                  <section>
                    <p className="text-xs text-[#8fa09e] mb-2">期限なし・保管</p>
                    {noDeadline.map((doc) => (
                      <DocumentCard key={doc.id} {...doc} />
                    ))}
                  </section>
                )}

                {/* 完了済み */}
                {done.length > 0 && (
                  <section>
                    <p className="text-xs text-[#8fa09e] mb-2">完了済み</p>
                    {done.map((doc) => (
                      <DocumentCard key={doc.id} {...doc} />
                    ))}
                  </section>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}