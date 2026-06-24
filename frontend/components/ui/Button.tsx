import { type ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "accent" | "ghost" | "danger";
  loading?: boolean;
}

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  const variantStyles = {
    primary: { background: "#557C79", color: "#fff" },
    accent:  { background: "#D45D1E", color: "#fff" },
    ghost:   { background: "#D2D4BC", color: "#3a4a48" },
    danger:  { background: "#FCEBEB", color: "#E24B4A" },
  };

  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-medium text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed ${className ?? ""}`}
      style={variantStyles[variant]}
    >
      {loading ? (
        <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z" />
        </svg>
      ) : null}
      {children}
    </button>
  );
}