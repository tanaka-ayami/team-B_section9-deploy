"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { BottomNav } from "@/components/layout/BottomNav";
import { AppHeader } from "@/components/layout/AppHeader";
import { NotificationDrawer } from "@/components/layout/NotificationDrawer";

// モック通知データ（Week2でAPI差し替え）
const MOCK_NOTIFICATIONS = [
  {
    id: "notif-001",
    message: "花子が書類を登録しました",
    documentTitle: "夏期講習 申込書",
    isRead: false,
    createdAt: "2026-06-27T10:00:00Z",
  },
  {
    id: "notif-002",
    message: "太郎が書類を登録しました",
    documentTitle: "定期健康診断のご案内",
    isRead: false,
    createdAt: "2026-06-26T15:30:00Z",
  },
  {
    id: "notif-003",
    message: "花子が書類を登録しました",
    documentTitle: "PTA会費 納入のお知らせ",
    isRead: true,
    createdAt: "2026-06-25T09:00:00Z",
  },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS);

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-screen">
        <svg className="w-8 h-8 animate-spin text-primary" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z" />
        </svg>
      </div>
    );
  }

  const handleNotificationRead = (id: string) => {
    // Week2でPATCH /v1/notifications/:id/read に差し替え
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-screen">
      <AppHeader
        unreadCount={unreadCount}
        onBellClick={() => setDrawerOpen(true)}
      />
      <main className="flex-1 pb-24">{children}</main>
      <BottomNav />
      <NotificationDrawer
        open={drawerOpen}
        notifications={notifications}
        onClose={() => setDrawerOpen(false)}
        onRead={handleNotificationRead}
      />
    </div>
  );
}