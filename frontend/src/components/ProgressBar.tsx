export function ProgressBar({ done, total }: { done: number; total: number }) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return (
    <div style={{ marginTop: "1rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "0.85rem",
          color: "#aaa",
        }}
      >
        <span>Processing…</span>
        <span>
          {done} / {total} ({pct}%)
        </span>
      </div>
      <div
        style={{
          background: "#1a1a1a",
          borderRadius: "4px",
          height: "8px",
          marginTop: "0.4rem",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: "#3b82f6",
            transition: "width 0.4s ease",
          }}
        />
      </div>
    </div>
  );
}
