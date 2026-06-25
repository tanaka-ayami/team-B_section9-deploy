// frontend/components/calendar/DeadlineBadge.tsx
import dayjs from "dayjs";

interface DeadlineBadgeProps {
  deadlineDate: string; // "YYYY-MM-DD"
  isDone: boolean;
}

type BadgeVariant = "today" | "urgent" | "normal" | "done";

function getVariant(deadlineDate: string, isDone: boolean): BadgeVariant {
  if (isDone) return "done";
  const diff = dayjs(deadlineDate).diff(dayjs().startOf("day"), "day");
  if (diff === 0) return "today";
  if (diff <= 3) return "urgent";
  return "normal";
}

const STYLES: Record <
  BadgeVariant,
  { label: (diff: number) => string; style: React.CSSProperties }
> = {
  today:  { label: () => "今日！",       style: { backgroundColor: "#D45D1E", color: "#fff",     fontWeight: 600 } },
  urgent: { label: (d) => `あと${d}日`, style: { backgroundColor: "#FADDCC", color: "#D45D1E"} },
  normal: { label: (d) => `あと${d}日`, style: { backgroundColor: "#ADCFBA", color: "#2d5a4e" } },
  done:   { label: () => "✓ 済",         style: { backgroundColor: "#e8e8e8", color: "#aaa",     textDecoration: "line-through" } },
};

export function DeadlineBadge({ deadlineDate, isDone }: DeadlineBadgeProps) {
  const variant = getVariant(deadlineDate, isDone);
  const diff = dayjs(deadlineDate).diff(dayjs().startOf("day"), "day");
  const { label, style } = STYLES[variant];

  return (
    <span
      className="text-xs px-2 py-0.5 rounded-full whitespace-nowrap"
      style={style}
    >
      {label(diff)}
    </span>
  );
}