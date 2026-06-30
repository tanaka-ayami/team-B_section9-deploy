"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { BottomNav } from "@/components/layout/BottomNav";
import { AppHeader } from "@/components/layout/AppHeader";
import { NotificationDrawer } from "@/components/layout/NotificationDrawer";
import { notificationApi, AppNotification } from "@/lib/api";

// NotificationDrawerが期待する形に変換する（バックエンドのAppNotificationとは少し項目名が違う）
interface DrawerNotification {
  id: string;
  message: string;
  documentTitle: string;
  isRead: boolean;
  createdAt: string;
}

function toDrawerNotification(n: AppNotification): DrawerNotification {
  return {
    id: n.id,
    message: n.message,
    documentTitle: "", // バックエンドのレスポンスにはdocument_idしか無いため、現時点では空欄
    isRead: n.is_read,
    createdAt: n.created_at,
  };
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifications, setNotifications] = useState<DrawerNotification[]>([]);
  const unreadCount = notifications.filter((n) => !n.isRead).length;

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  // ログイン済みになったら通知一覧を取得する
  useEffect(() => {
    if (!loading && user) {
      notificationApi
        .list()
        .then((list) => setNotifications(list.map(toDrawerNotification)))
        .catch(() => setNotifications([]));
    }
  }, [loading, user]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-screen">
        <svg
          className="w-8 h-8 animate-spin text-primary"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z"
          />
        </svg>
      </div>
    );
  }

  const handleNotificationRead = (id: string) => {
    // 画面側は即時反映（楽観的更新）し、APIへの反映は裏側で行う
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n)),
    );
    notificationApi.markRead(id).catch(() => {
      // 失敗した場合は既読状態を元に戻す
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isRead: false } : n)),
      );
    });
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
