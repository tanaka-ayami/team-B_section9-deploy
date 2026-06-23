"use client";

import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";

interface CalendarEvent {
  id: string;
  title: string;
  date: string;       // "YYYY-MM-DD"
  isDone: boolean;
}

interface CalendarViewProps {
  events?: CalendarEvent[];
  onMonthChange?: (year: number, month: number) => void;
}

export function CalendarView({
  events = [],
  onMonthChange,
}: CalendarViewProps) {
  const fcEvents = events.map((e) => ({
    id: e.id,
    title: e.title,
    date: e.date,
    classNames: e.isDone ? ["fc-event-done"] : [],
  }));

  return (
    <div className="px-4 pt-2">
      <style>{`
        .fc-event-done { opacity: 0.4; }
        .fc .fc-toolbar-title { font-size: 1rem; font-weight: 500; }
        .fc .fc-button {
          background-color: #4A7C59 !important;
          border-color: #4A7C59 !important;
          font-size: 0.75rem;
        }
        .fc .fc-daygrid-day.fc-day-today { background-color: #EEF1EC; }
      `}</style>
      <FullCalendar
        plugins={[dayGridPlugin]}
        initialView="dayGridMonth"
        locale="ja"
        events={fcEvents}
        headerToolbar={{
          left: "prev",
          center: "title",
          right: "next",
        }}
        height="auto"
        datesSet={(info) => {
          if (onMonthChange) {
            const d = info.view.currentStart;
            onMonthChange(d.getFullYear(), d.getMonth() + 1);
          }
        }}
      />
    </div>
  );
}