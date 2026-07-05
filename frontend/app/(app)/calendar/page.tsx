"use client";

import { useEffect, useState } from "react";
import { CalendarView } from "@/components/calendar/CalendarView";
import { DocumentCard } from "@/components/calendar/DocumentCard";
import { FAB } from "@/components/layout/FAB";
import { groupApi, documentApi, categoryApi, Document, Category } from "@/lib/api";

interface DisplayDocument {
  id: string;
  title: string;
  categoryName?: string;
  categoryIcon?: string;
  createdByName?: string;
  deadlineDate?: string;
  hasDeadline: boolean;
  isDone: boolean;
}

export default function CalendarPage() {
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [documents, setDocuments] = useState<DisplayDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      try {
        const [groups, categories] = await Promise.all([
          groupApi.list(),
          categoryApi.list(),
        ]);
        const categoryIconById = new Map<string, string>(
          categories.map((c: Category) => [c.id, c.icon ?? "📄"])
        );

        const [docsByGroup, membersByGroup] = await Promise.all([
          Promise.all(groups.map((g) => documentApi.list(g.id))),
          Promise.all(groups.map((g) => groupApi.getMembers(g.id))),
        ]);

        const displayNameByUserId = new Map<string, string>();
        membersByGroup.flat().forEach((m) => {
          displayNameByUserId.set(m.user_id, m.display_name);
        });

        const allDocs: DisplayDocument[] = docsByGroup.flat().map((d: Document) => ({
          id: d.id,
          title: d.title ?? "(無題)",
          categoryName: d.categoryName ?? undefined,
          categoryIcon: d.category_id ? categoryIconById.get(d.category_id) : undefined,
          createdByName: displayNameByUserId.get(d.created_by),
          deadlineDate: d.deadline_date ?? undefined,
          hasDeadline: d.has_deadline,
          isDone: d.is_done,
        }));

        if (!cancelled) setDocuments(allDocs);
      } catch (e) {
        if (!cancelled) setDocuments([]);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();

    // router.back() はブラウザ履歴操作なので popstate で検知
    const handlePopState = () => load();
    window.addEventListener("popstate", handlePopState);

    return () => {
      cancelled = true;
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  const calendarEvents = documents
    .filter((d) => d.hasDeadline && d.deadlineDate)
    .map((d) => ({
      id: d.id,
      title: d.title,
      date: d.deadlineDate as string,
      isDone: d.isDone,
    }));

  const monthlyDocuments = documents
    .filter((d) => {
      if (!d.deadlineDate) return false;
      const [y, m] = d.deadlineDate.split("-").map(Number);
      return y === currentYear && m === currentMonth;
    })
    .sort((a, b) => {
      if (a.isDone !== b.isDone) return a.isDone ? 1 : -1;
      return a.deadlineDate! < b.deadlineDate! ? -1 : 1;
    });
  return (
    <div className="min-h-screen bg-[#f2f1ec]">
      <div className="px-4 pt-4">
        <div className="bg-white rounded-[18px] overflow-hidden">
          <CalendarView
            events={calendarEvents}
            onMonthChange={(y, m) => {
              setCurrentYear(y);
              setCurrentMonth(m);
            }}
          />
        </div>
      </div>
      <section className="px-4 pt-4 pb-28">
        <p className="text-xs mb-3 text-[#557C79] opacity-60">
          {currentYear}年{currentMonth}月の書類
        </p>
        {isLoading ? (
          <p className="text-sm text-center py-8 text-[#8fa09e]">読み込み中...</p>
        ) : monthlyDocuments.length === 0 ? (
          <p className="text-sm text-center py-8 text-[#8fa09e]">
            この月の書類はありません
          </p>
        ) : (
          monthlyDocuments.map((doc) => (
            <DocumentCard key={doc.id} {...doc} />
          ))
        )}
      </section>
      <FAB />
    </div>
  );
}