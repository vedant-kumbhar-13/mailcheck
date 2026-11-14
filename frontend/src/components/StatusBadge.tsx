import type { SingleResult } from "../api/single";

const COLORS: Record<SingleResult["status"], string> = {
  valid: "#22c55e",
  risky: "#f59e0b",
  invalid: "#ef4444",
  unknown: "#94a3b8",
};

export function StatusBadge({ status }: { status: SingleResult["status"] }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.25rem 0.75rem",
        borderRadius: "9999px",
        background: COLORS[status],
        color: "#fff",
        fontWeight: 700,
        fontSize: "0.85rem",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      {status}
    </span>
  );
}
