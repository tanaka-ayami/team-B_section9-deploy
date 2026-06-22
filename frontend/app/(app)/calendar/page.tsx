"use client";

import { AppHeader } from "@/components/layout/AppHeader";

export default function CalendarPage() {
  return (
    <div>
      <AppHeader
        groupName="山田ファミリー"
        yearMonth="2026年6月"
        unreadCount={2}
      />
      <div className="p-4">
        <p className="text-sm text-center mt-8" style={{ color: "#6B7C6F" }}>
          カレンダーを実装予定
        </p>
      </div>
    </div>
  );
}