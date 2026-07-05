"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

interface Notification {
  id: string;
  message: string;
  documentTitle: string;
  isRead: boolean;
  createdAt: string;
}

interface NotificationDrawerProps {
  open: boolean;
  notifications: Notification[];
  onClose: () => void;
  onRead: (id: string) => void;
}

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "たった今";
  if (minutes < 60) return `${minutes}分前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}時間前`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "昨日";
  return `${days}日前`;
}

export function NotificationDrawer({
  open,
  notifications,
  onClose,
  onRead,
}: NotificationDrawerProps) {
  const router = useRouter();

  // ドロワーが開いているときは背景スクロールを無効化
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  const handleNotificationClick = (notif: Notification) => {
    onRead(notif.id);
    onClose();
    // Week2で書類詳細へ遷移（document_idが取れたら /documents/:id に変更）
    router.push("/calendar");
  };

  return (
    <>
      {/* オーバーレイ */}
      <div
        className="fixed inset-0 z-40 bg-black/40"
        onClick={onClose}
      />

      {/* ドロワー本体 */}
      <div className="fixed top-0 right-0 bottom-0 z-50 w-[88%] max-w-sm bg-white shadow-xl flex flex-col">
        {/* ヘッダー */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-[#D2D4BC]">
          <h2 className="text-base font-semibold text-white px-3 py-1.5 rounded-lg inline-block" style={{ backgroundColor: "#557C79" }}>お知らせ</h2>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[#f2f1ec]"
            aria-label="閉じる"
          >
            <svg className="w-5 h-5 text-[#557C79]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 通知リスト */}
        <div className="flex-1 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-[#8fa09e]">
              <svg className="w-12 h-12 opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
              </svg>
              <p className="text-sm">お知らせはありません</p>
            </div>
          ) : (
            <ul>
              {notifications.map((notif) => (
                <li key={notif.id}>
                  <button
                    type="button"
                    onClick={() => handleNotificationClick(notif)}
                    className="w-full text-left px-4 py-4 border-b border-[#f2f1ec] flex gap-3 items-start transition-colors hover:bg-[#f2f1ec]"
                    style={{
                      backgroundColor: notif.isRead ? "transparent" : "#FFF8F5",
                    }}
                  >
                    {/* 未読ドット */}
                    <span className="mt-1.5 flex-shrink-0 w-2 h-2 rounded-full"
                      style={{ backgroundColor: notif.isRead ? "transparent" : "#D45D1E" }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-[#1F2D24]">{notif.message}</p>
                      <p className="text-xs mt-0.5 text-[#557C79] truncate">{notif.documentTitle}</p>
                      <p className="text-xs mt-1 text-[#8fa09e]">
                        {formatRelativeTime(notif.createdAt)}
                      </p>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
}