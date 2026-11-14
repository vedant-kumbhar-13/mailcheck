export function ChecksTable({ checks }: { checks: Record<string, string> }) {
  const ICON: Record<string, string> = { pass: "✅", fail: "❌", error: "⚠️", skip: "–" };
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
      <thead>
        <tr>
          <th style={{ textAlign: "left", padding: "0.4rem 0.8rem", borderBottom: "1px solid #333" }}>Check</th>
          <th style={{ textAlign: "left", padding: "0.4rem 0.8rem", borderBottom: "1px solid #333" }}>Result</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(checks).map(([k, v]) => (
          <tr key={k}>
            <td style={{ padding: "0.4rem 0.8rem", textTransform: "capitalize" }}>{k}</td>
            <td style={{ padding: "0.4rem 0.8rem" }}>{ICON[v] ?? v} {v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
