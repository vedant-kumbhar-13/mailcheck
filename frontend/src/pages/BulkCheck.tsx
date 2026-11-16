import { useRef, useState } from "react";

import { deleteJob, submitBulk } from "../api/bulk";
import { ProgressBar } from "../components/ProgressBar";
import { ResultsTable } from "../components/ResultsTable";
import { useJobPoller } from "../hooks/useJobPoller";

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
            Upload &amp; Validate
          </button>
        </form>
      )}

      {submitError && (
        <p style={{ color: "#ef4444", marginTop: "1rem" }}>Error: {submitError}</p>
      )}
      {pollError && (
        <p style={{ color: "#ef4444", marginTop: "1rem" }}>Poll error: {pollError}</p>
      )}

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
                  fetch(`/api/jobs/${jobId}/download`, {
                    headers: { "X-Job-Key": jobKey },
                  })
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
