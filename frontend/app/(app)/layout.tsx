// frontend/app/(app)/layout.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { BottomNav } from "@/components/layout/BottomNav";
import { AppHeader } from "@/components/layout/AppHeader";
import { NotificationDrawer } from "@/components/layout/NotificationDrawer";
import { notificationApi, AppNotification } from "@/lib/api";

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
    documentTitle: "",
    isRead: n.is_read,
    createdAt: n.created_at,
  };
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const isFullscreen = pathname === "/scan";
  // 共通ヘッダー（Scanly ロゴ＋ベルマーク）を表示するのは、ボトムナビの3つのトップ画面のみ。
  // それ以外（詳細・編集・確認・新規作成などの下層ページ）は自前のヘッダー（戻る＋タイトル）を持つため、
  // 共通ヘッダーは非表示にする。
  const topLevelPaths = ["/calendar", "/documents", "/settings"];
  const hasOwnHeader = !isFullscreen && !topLevelPaths.includes(pathname);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifications, setNotifications] = useState<DrawerNotification[]>([]);
  const unreadCount = notifications.filter((n) => !n.isRead).length;

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

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
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n)),
    );
    notificationApi.markRead(id).catch(() => {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isRead: false } : n)),
      );
    });
  };

  if (isFullscreen) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen flex flex-col bg-screen">
      {!hasOwnHeader && (
        <AppHeader
          unreadCount={unreadCount}
          onBellClick={() => setDrawerOpen(true)}
        />
      )}
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