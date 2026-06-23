"use client";

import { useState } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { CalendarView } from "@/components/calendar/CalendarView";
import { DocumentCard } from "@/components/calendar/DocumentCard";
import { FAB } from "@/components/layout/FAB";

const MOCK_DOCUMENTS = [
  {
    id: "doc-001",
    title: "夏期講習 申込書",
    categoryName: "学校",
    createdByName: "花子",
    deadlineDate: "2026-06-26",
    hasDeadline: true,
    isDone: false,
  },
  {
    id: "doc-002",
    title: "PTA会費 納入のお知らせ",
    categoryName: "保険",
    createdByName: "花子",
    deadlineDate: "2026-06-30",
    hasDeadline: true,
    isDone: false,
  },
  {
    id: "doc-003",
    title: "定期健康診断のご案内",
    categoryName: "医療",
    createdByName: "太郎",
    deadlineDate: "2026-06-24",
    hasDeadline: true,
    isDone: true,
  },
];

export default function CalendarPage() {
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);

  const calendarEvents = MOCK_DOCUMENTS
    .filter((d) => d.hasDeadline && d.deadlineDate)
    .map((d) => ({
      id: d.id,
      title: d.title,
      date: d.deadlineDate,
      isDone: d.isDone,
    }));

  const monthlyDocuments = MOCK_DOCUMENTS.filter((d) => {
    if (!d.deadlineDate) return false;
    const [y, m] = d.deadlineDate.split("-").map(Number);
    return y === currentYear && m === currentMonth;
  });

  return (
    <div className="min-h-screen bg-[#f2f1ec]">
      <AppHeader
        groupName="山田ファミリー"
        yearMonth={`${currentYear}年${currentMonth}月`}
        unreadCount={2}
      />
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
      <section className="px-4 pt-4 pb-2">
        <p className="text-xs mb-3 text-[#557C79] opacity-60">
          {currentYear}年{currentMonth}月の書類
        </p>
        {monthlyDocuments.length === 0 ? (
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