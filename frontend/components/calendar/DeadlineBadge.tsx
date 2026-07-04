// frontend/components/calendar/DeadlineBadge.tsx
import dayjs from "dayjs";

interface DeadlineBadgeProps {
  deadlineDate: string; // "YYYY-MM-DD"
  isDone: boolean;
}

type BadgeVariant = "expired" | "today" | "urgent" | "normal" | "done";

function getVariant(deadlineDate: string, isDone: boolean): BadgeVariant {
  if (isDone) return "done";
  const diff = dayjs(deadlineDate).diff(dayjs().startOf("day"), "day");
  if (diff < 0) return "expired";
  if (diff === 0) return "today";
  if (diff <= 3) return "urgent";
  return "normal";
}

const STYLES: Record<BadgeVariant, { label: (diff: number) => string; style: React.CSSProperties }> = {
  expired: { label: () => "期限切れ",     style: { color: "#D93025", fontWeight: 600, backgroundColor: "transparent" } },
  today:   { label: () => "今日！",       style: { backgroundColor: "#DC2626", color: "#fff",     fontWeight: 600 } },
  urgent:  { label: (d) => `あと${d}日`, style: { backgroundColor: "#F5C29B", color: "#8A3510"} },
  normal:  { label: (d) => `あと${d}日`, style: { backgroundColor: "#9BBFAA", color: "#1e4d3a" } },
  done:    { label: () => "済",           style: { backgroundColor: "#C0C0C0", color: "#555" } },
};

export function DeadlineBadge({ deadlineDate, isDone }: DeadlineBadgeProps) {
  const variant = getVariant(deadlineDate, isDone);
  const diff = dayjs(deadlineDate).diff(dayjs().startOf("day"), "day");
  const { label, style } = STYLES[variant];

  return (
    <span className="inline-flex items-center gap-1 whitespace-nowrap">
      {variant === "done" && (
        <span className="text-sm font-bold" style={{ color: "#557C79" }}>✔</span>
      )}
      {variant === "today" && (
        <span className="text-sm font-bold" style={{ color: "#DC2626" }}>⚠</span>
      )}
      <span className="text-xs px-2 py-0.5 rounded-full" style={style}>
        {label(diff)}
      </span>
    </span>
  );
}