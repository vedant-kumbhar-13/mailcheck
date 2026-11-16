import { useState } from "react";

import { type BulkResult, getResults } from "../api/bulk";
import { StatusBadge } from "./StatusBadge";

const STATUS_FILTER = ["all", "valid", "risky", "invalid", "unknown"] as const;
type FilterOption = (typeof STATUS_FILTER)[number];

const PAGE_SIZE = 100;

export function ResultsTable({
  jobId,
  jobKey,
  total,
}: {
  jobId: string;
  jobKey: string;
  total: number;
}) {
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState<BulkResult[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [filter, setFilter] = useState<FilterOption>("all");

  async function load(p: number) {
    const data = await getResults(jobId, jobKey, p, PAGE_SIZE);
    setRows(data.results);
    setPage(p);
    setLoaded(true);
  }

  if (!loaded) {
    return (
      <button
        onClick={() => load(1)}
        style={{
          marginTop: "1rem",
          padding: "0.5rem 1rem",
          borderRadius: "6px",
          border: "none",
          background: "#3b82f6",
          color: "#fff",
          cursor: "pointer",
        }}
      >
        Load Results
      </button>
    );
  }

  const displayed = filter === "all" ? rows : rows.filter((r) => r.status === filter);
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div style={{ marginTop: "1.5rem" }}>
      {/* Filter bar */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        {STATUS_FILTER.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              padding: "0.25rem 0.75rem",
              borderRadius: "9999px",
              border: "1px solid #333",
              background: filter === s ? "#3b82f6" : "#1a1a1a",
              color: "#e8e8e8",
              cursor: "pointer",
              fontSize: "0.8rem",
              textTransform: "capitalize",
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #333" }}>
              {["Address", "Status", "Disposable", "Role", "Domain"].map((h) => (
                <th
                  key={h}
                  style={{ padding: "0.5rem 0.75rem", textAlign: "left", color: "#aaa" }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayed.map((row, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #222" }}>
                <td style={{ padding: "0.4rem 0.75rem" }}>{row.address}</td>
                <td style={{ padding: "0.4rem 0.75rem" }}>
                  <StatusBadge status={row.status} />
                </td>
                <td style={{ padding: "0.4rem 0.75rem" }}>{row.is_disposable ? "Yes" : "No"}</td>
                <td style={{ padding: "0.4rem 0.75rem" }}>{row.is_role ? "Yes" : "No"}</td>
                <td style={{ padding: "0.4rem 0.75rem", color: "#888" }}>{row.domain}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem", alignItems: "center" }}>
        <button
          disabled={page <= 1}
          onClick={() => load(page - 1)}
          style={{ padding: "0.3rem 0.75rem", cursor: page > 1 ? "pointer" : "not-allowed" }}
        >
          ← Prev
        </button>
        <span style={{ fontSize: "0.85rem", color: "#aaa" }}>
          Page {page} of {totalPages}
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => load(page + 1)}
          style={{
            padding: "0.3rem 0.75rem",
            cursor: page < totalPages ? "pointer" : "not-allowed",
          }}
        >
          Next →
        </button>
      </div>
    </div>
  );
}
