# C4 — Bulk UI
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Sonnet 4.6 Thinking**
**Prerequisite: C2 AND C3 exit gates both green.**

---

## PROMPT (copy everything below this line)

---

You are a senior TypeScript/React engineer. We are building **MailCheck**. This is **Chunk 4 – Bulk UI**: add the React UI for CSV upload, job status polling, paginated results display, CSV download, and job deletion.

### What already exists

- `frontend/src/api/single.ts` — single-check API
- `frontend/src/pages/SingleCheck.tsx` — single-check page
- `frontend/src/App.tsx` — renders SingleCheck

The backend bulk endpoints are live:
- `POST /api/validations/bulk` (multipart/form-data, field: `file`)
- `GET /api/jobs/{id}` (header: `X-Job-Key`)
- `GET /api/jobs/{id}/results?page=1&page_size=100` (header: `X-Job-Key`)
- `GET /api/jobs/{id}/download` (header: `X-Job-Key`)
- `DELETE /api/jobs/{id}` (header: `X-Job-Key`)

### New files to create

#### 1. `frontend/src/api/bulk.ts`

```typescript
export interface JobMeta {
  job_id: string;
  job_key: string;
  total: number;
  status: "pending" | "running" | "ready" | "failed";
  done: number;
  error?: string;
}

export interface BulkResult {
  address: string;
  status: "valid" | "invalid" | "risky" | "unknown";
  is_disposable: boolean;
  is_role: boolean;
  domain: string;
  checks: Record<string, string>;
}

export interface ResultPage {
  total: number;
  done: number;
  page: number;
  page_size: number;
  results: BulkResult[];
}

export async function submitBulk(file: File): Promise<JobMeta> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/validations/bulk", { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.error ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getJobStatus(jobId: string, jobKey: string): Promise<JobMeta> {
  const res = await fetch(`/api/jobs/${jobId}`, {
    headers: { "X-Job-Key": jobKey },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getResults(
  jobId: string,
  jobKey: string,
  page: number,
  pageSize = 100
): Promise<ResultPage> {
  const res = await fetch(
    `/api/jobs/${jobId}/results?page=${page}&page_size=${pageSize}`,
    { headers: { "X-Job-Key": jobKey } }
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function deleteJob(jobId: string, jobKey: string): Promise<void> {
  await fetch(`/api/jobs/${jobId}`, {
    method: "DELETE",
    headers: { "X-Job-Key": jobKey },
  });
}

export function downloadUrl(jobId: string, jobKey: string): string {
  return `/api/jobs/${jobId}/download`;
}
```

#### 2. `frontend/src/hooks/useJobPoller.ts`

```typescript
import { useState, useEffect, useRef } from "react";
import { getJobStatus, type JobMeta } from "../api/bulk";

/**
 * Polls GET /api/jobs/{id} every 2 seconds until status is ready or failed.
 * Stops automatically when terminal state is reached.
 */
export function useJobPoller(jobId: string | null, jobKey: string | null) {
  const [meta, setMeta] = useState<JobMeta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId || !jobKey) return;

    const poll = async () => {
      try {
        const m = await getJobStatus(jobId, jobKey);
        setMeta(m);
        if (m.status === "ready" || m.status === "failed") {
          if (timerRef.current) clearInterval(timerRef.current);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Poll failed");
        if (timerRef.current) clearInterval(timerRef.current);
      }
    };

    poll(); // immediate first check
    timerRef.current = setInterval(poll, 2000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [jobId, jobKey]);

  return { meta, error };
}
```

#### 3. `frontend/src/components/ProgressBar.tsx`

```tsx
export function ProgressBar({ done, total }: { done: number; total: number }) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return (
    <div style={{ marginTop: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#aaa" }}>
        <span>Processing…</span>
        <span>{done} / {total} ({pct}%)</span>
      </div>
      <div style={{ background: "#1a1a1a", borderRadius: "4px", height: "8px", marginTop: "0.4rem", overflow: "hidden" }}>
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
```

#### 4. `frontend/src/components/ResultsTable.tsx`

```tsx
import { useState } from "react";
import { getResults, type BulkResult } from "../api/bulk";
import { StatusBadge } from "./StatusBadge";

const STATUS_FILTER = ["all", "valid", "risky", "invalid", "unknown"] as const;

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
  const [filter, setFilter] = useState<(typeof STATUS_FILTER)[number]>("all");
  const PAGE_SIZE = 100;

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
                <th key={h} style={{ padding: "0.5rem 0.75rem", textAlign: "left", color: "#aaa" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayed.map((row, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #222" }}>
                <td style={{ padding: "0.4rem 0.75rem" }}>{row.address}</td>
                <td style={{ padding: "0.4rem 0.75rem" }}><StatusBadge status={row.status} /></td>
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
        <button disabled={page <= 1} onClick={() => load(page - 1)} style={{ padding: "0.3rem 0.75rem", cursor: page > 1 ? "pointer" : "not-allowed" }}>← Prev</button>
        <span style={{ fontSize: "0.85rem", color: "#aaa" }}>Page {page} of {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => load(page + 1)} style={{ padding: "0.3rem 0.75rem", cursor: page < totalPages ? "pointer" : "not-allowed" }}>Next →</button>
      </div>
    </div>
  );
}
```

#### 5. `frontend/src/pages/BulkCheck.tsx`

```tsx
import { useState, useRef } from "react";
import { submitBulk, deleteJob } from "../api/bulk";
import { useJobPoller } from "../hooks/useJobPoller";
import { ProgressBar } from "../components/ProgressBar";
import { ResultsTable } from "../components/ResultsTable";

export function BulkCheck() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobKey, setJobKey] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const { meta, error: pollError } = useJobPoller(jobId, jobKey);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setSubmitError(null);
    try {
      const m = await submitBulk(file);
      setJobId(m.job_id);
      setJobKey(m.job_key);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Upload failed");
    }
  }

  async function handleDelete() {
    if (!jobId || !jobKey) return;
    setDeleting(true);
    await deleteJob(jobId, jobKey).catch(() => null);
    setJobId(null);
    setJobKey(null);
    setDeleting(false);
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <section style={{ marginTop: "3rem" }}>
      <h2 style={{ marginBottom: "1rem" }}>Bulk Email Check</h2>
      <p style={{ color: "#888", marginBottom: "1rem", fontSize: "0.9rem" }}>
        Upload a CSV file with an <code>email</code> column. Max 1,000 rows, 2 MB.
      </p>

      {!jobId && (
        <form onSubmit={handleUpload} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,text/csv"
            required
            style={{ flex: 1, color: "#e8e8e8" }}
          />
          <button
            type="submit"
            style={{
              padding: "0.6rem 1.5rem",
              borderRadius: "6px",
              border: "none",
              background: "#3b82f6",
              color: "#fff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Upload & Validate
          </button>
        </form>
      )}

      {submitError && <p style={{ color: "#ef4444", marginTop: "1rem" }}>Error: {submitError}</p>}
      {pollError && <p style={{ color: "#ef4444", marginTop: "1rem" }}>Poll error: {pollError}</p>}

      {meta && (
        <div style={{ marginTop: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span style={{ fontWeight: 700 }}>
              Status: <span style={{ textTransform: "uppercase" }}>{meta.status}</span>
            </span>
            {(meta.status === "ready" || meta.status === "failed") && (
              <button
                onClick={handleDelete}
                disabled={deleting}
                style={{
                  padding: "0.3rem 0.75rem",
                  borderRadius: "6px",
                  border: "1px solid #555",
                  background: "transparent",
                  color: "#ef4444",
                  cursor: "pointer",
                  fontSize: "0.85rem",
                }}
              >
                {deleting ? "Deleting…" : "Delete Results"}
              </button>
            )}
            {meta.status === "ready" && jobId && jobKey && (
              <a
                href={`/api/jobs/${jobId}/download`}
                download
                style={{ color: "#3b82f6", fontSize: "0.85rem" }}
                onClick={(e) => {
                  // Add key header via fetch; plain <a> can't set headers
                  e.preventDefault();
                  fetch(`/api/jobs/${jobId}/download`, { headers: { "X-Job-Key": jobKey } })
                    .then((r) => r.blob())
                    .then((blob) => {
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `mailcheck_${jobId.slice(0, 8)}.csv`;
                      a.click();
                      URL.revokeObjectURL(url);
                    });
                }}
              >
                ⬇ Download CSV
              </a>
            )}
          </div>

          {(meta.status === "pending" || meta.status === "running") && (
            <ProgressBar done={meta.done} total={meta.total} />
          )}

          {meta.status === "failed" && (
            <p style={{ color: "#ef4444", marginTop: "1rem" }}>
              Job failed: {meta.error ?? "Unknown error"}
            </p>
          )}

          {meta.status === "ready" && jobId && jobKey && (
            <ResultsTable jobId={jobId} jobKey={jobKey} total={meta.total} />
          )}
        </div>
      )}
    </section>
  );
}
```

#### 6. `frontend/src/App.tsx` — add BulkCheck tab

```tsx
import { useState } from "react";
import { SingleCheck } from "./pages/SingleCheck";
import { BulkCheck } from "./pages/BulkCheck";

const TABS = ["single", "bulk"] as const;

export default function App() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("single");

  return (
    <main className="app">
      <header style={{ marginBottom: "2rem" }}>
        <h1>MailCheck</h1>
        <p style={{ color: "#888", marginTop: "0.25rem" }}>Privacy-first email validation</p>
      </header>

      <nav style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem" }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: "0.5rem 1.25rem",
              borderRadius: "6px",
              border: "none",
              background: tab === t ? "#3b82f6" : "#1a1a1a",
              color: tab === t ? "#fff" : "#aaa",
              cursor: "pointer",
              fontWeight: tab === t ? 700 : 400,
              textTransform: "capitalize",
            }}
          >
            {t === "single" ? "Single Check" : "Bulk Check (CSV)"}
          </button>
        ))}
      </nav>

      {tab === "single" && <SingleCheck />}
      {tab === "bulk" && <BulkCheck />}
    </main>
  );
}
```

---

### Manual test scenario

After starting both backend and frontend:

1. Create a file called `test_emails.csv` with this content:
```csv
email
user@gmail.com
admin@mailinator.com
noreply@example.com
notanemail
test@nonexistentdomain12345.xyz
```

2. Open `http://localhost:5173`, click **Bulk Check (CSV)** tab.
3. Upload `test_emails.csv`, click **Upload & Validate**.
4. Watch the progress bar fill.
5. When status shows READY, click **Load Results**.
6. Check that:
   - `user@gmail.com` → `valid` or `unknown`
   - `admin@mailinator.com` → `risky`
   - `noreply@example.com` → `risky`
   - `notanemail` → `invalid`
7. Click **Download CSV** → CSV file downloads.
8. Click **Delete Results** → table disappears.

---

### Exit gate for C4

- [ ] Upload a CSV → job_id and job_key stored in React state (not in localStorage)
- [ ] Progress bar visible while RUNNING
- [ ] Results table loads when READY
- [ ] Status filter buttons work (click "risky" → only risky rows visible)
- [ ] Download CSV button downloads the file
- [ ] Delete Results button removes the job
- [ ] No results stored in localStorage or sessionStorage (open DevTools → Application → Storage → verify empty)
- [ ] Git commit: `git commit -m "C4: bulk UI – upload, polling, results table, download"`
