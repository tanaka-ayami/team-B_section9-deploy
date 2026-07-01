"use client";

interface AppHeaderProps {
  groupName?: string;
  yearMonth?: string;
  unreadCount?: number;
  onBellClick?: () => void;
}

export function AppHeader({
  groupName = "",
  yearMonth = "",
  unreadCount = 0,
  onBellClick,
}: AppHeaderProps) {
  return (
    <header className="px-4 pt-4 pb-4 bg-[#557C79]">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-medium text-white leading-tight tracking-wider">
            Scanly
        </h1>
          {(groupName || yearMonth) && (
            <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.75)" }}>
              {[groupName, yearMonth].filter(Boolean).join("・")}
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={onBellClick}
          aria-label="お知らせ"
          className="relative w-9 h-9 rounded-full flex items-center justify-center"
          style={{ background: "rgba(255,255,255,0.2)" }}
        >
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
          </svg>
          {unreadCount > 0 && (
            <span
              className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full flex items-center justify-center text-white bg-[#D45D1E]"
              style={{ fontSize: "10px", fontWeight: 500 }}
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}