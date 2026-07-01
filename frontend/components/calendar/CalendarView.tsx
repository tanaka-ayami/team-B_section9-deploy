// frontend/components/calendar/CalendarView.tsx
"use client";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import dayjs from "dayjs";

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
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
  const fcEvents = events.map((e) => {
    const diff = dayjs(e.date).diff(dayjs().startOf("day"), "day");
    const isToday = !e.isDone && diff === 0;
    const isUrgent = !e.isDone && diff > 0 && diff <= 3;
    return {
      id: e.id,
      title: e.title,
      date: e.date,
      classNames: e.isDone
        ? ["fc-event-done"]
        : isToday
          ? ["fc-event-today"]
          : isUrgent
            ? ["fc-event-urgent"]
            : ["fc-event-normal"],
    };
  });

  return (
    <div className="px-3 pt-2 pb-3">
      <style>{`
        .fc table,
        .fc th,
        .fc td,
        .fc .fc-scrollgrid,
        .fc .fc-scrollgrid-section > td,
        .fc .fc-col-header-cell {
          border: none !important;
          background: transparent !important;
        }
        .fc .fc-daygrid-body tr {
          border-bottom: 0.5px solid rgba(0,0,0,0.06) !important;
        }
        .fc .fc-daygrid-body tr:last-child {
          border-bottom: none !important;
        }
        .fc .fc-toolbar { margin-bottom: 8px; }
        .fc .fc-toolbar-title { font-size: 0.95rem; font-weight: 500; color: #333; }
        .fc .fc-button {
          background: transparent !important;
          border: none !important;
          color: #557C79 !important;
          padding: 2px 6px !important;
          font-size: 1rem;
          box-shadow: none !important;
        }
        .fc .fc-button:focus { box-shadow: none !important; }
        .fc .fc-col-header-cell-cushion {
          font-size: 0.7rem;
          font-weight: 500;
          color: #888;
          padding: 4px 0;
          text-decoration: none !important;
        }
        .fc .fc-col-header-cell:first-child .fc-col-header-cell-cushion { color: #e05252; }
        .fc .fc-col-header-cell:last-child  .fc-col-header-cell-cushion { color: #4472c4; }
        .fc .fc-daygrid-day-top { justify-content: center; }
        .fc .fc-daygrid-day-number {
          font-size: 0.75rem;
          color: #333;
          text-decoration: none !important;
          width: 26px;
          height: 26px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          margin: 3px auto 1px;
        }
        .fc .fc-daygrid-day-number::after { content: none !important; }
        .fc-direction-ltr .fc-daygrid-day-number { float: none; }
        .fc .fc-day-sun .fc-daygrid-day-number { color: #e05252; }
        .fc .fc-day-sat .fc-daygrid-day-number { color: #4472c4; }
        .fc .fc-day-other .fc-daygrid-day-number { color: #ccc; }
        .fc .fc-day-other { opacity: 1; }
        .fc .fc-day-today { background: transparent !important; }
        .fc .fc-day-today .fc-daygrid-day-number {
          background-color: #557C79 !important;
          color: #fff !important;
        }
        .fc .fc-daygrid-day-events { margin-top: 1px; padding: 0 2px 2px; }
        .fc .fc-event {
          border: none !important;
          border-radius: 4px !important;
          padding: 0px 3px !important;
          margin: 1px 1px !important;
          font-size: 0.6rem !important;
          line-height: 1.4 !important;
          color: inherit !important;
}
        .fc .fc-event-title  { font-size: 0.6rem !important; color: inherit !important; }
        .fc .fc-daygrid-event-dot { display: none !important; }
        .fc .fc-event.fc-event-today  { background-color: #D45D1E !important; color: #fff !important; font-weight: 400 !important; }
        .fc .fc-event.fc-event-today .fc-event-main { color: #fff !important; }
        .fc .fc-event.fc-event-urgent { background-color: #F5C29B !important; color: #6B2508 !important; font-weight: 500 !important; }
        .fc .fc-event.fc-event-urgent .fc-event-main { color: #6B2508 !important; }
        .fc .fc-event.fc-event-normal { background-color: #ADCFBA !important; color: #143d2e !important; font-weight: 500 !important; }
        .fc .fc-event.fc-event-normal .fc-event-main { color: #143d2e !important; }
        .fc .fc-event.fc-event-done   { background-color: #C0C0C0 !important; color: #555 !important; }
        .fc .fc-event.fc-event-done .fc-event-main { color: #555 !important; }
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
        dayHeaderFormat={{ weekday: "narrow" }}
        dayCellContent={(arg) => arg.dayNumberText.replace("日", "")}
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