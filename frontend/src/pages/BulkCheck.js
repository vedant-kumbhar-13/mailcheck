import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useRef, useState } from "react";
import { deleteJob, submitBulk } from "../api/bulk";
import { ProgressBar } from "../components/ProgressBar";
import { ResultsTable } from "../components/ResultsTable";
import { useJobPoller } from "../hooks/useJobPoller";
export function BulkCheck() {
    const fileRef = useRef(null);
    const [jobId, setJobId] = useState(null);
    const [jobKey, setJobKey] = useState(null);
    const [submitError, setSubmitError] = useState(null);
    const [deleting, setDeleting] = useState(false);
    const { meta, error: pollError } = useJobPoller(jobId, jobKey);
    async function handleUpload(e) {
        e.preventDefault();
        const file = fileRef.current?.files?.[0];
        if (!file)
            return;
        setSubmitError(null);
        try {
            const m = await submitBulk(file);
            setJobId(m.job_id);
            setJobKey(m.job_key);
        }
        catch (err) {
            setSubmitError(err instanceof Error ? err.message : "Upload failed");
        }
    }
    async function handleDelete() {
        if (!jobId || !jobKey)
            return;
        setDeleting(true);
        await deleteJob(jobId, jobKey).catch(() => null);
        setJobId(null);
        setJobKey(null);
        setDeleting(false);
        if (fileRef.current)
            fileRef.current.value = "";
    }
    return (_jsxs("section", { style: { marginTop: "3rem" }, children: [_jsx("h2", { style: { marginBottom: "1rem" }, children: "Bulk Email Check" }), _jsxs("p", { style: { color: "#888", marginBottom: "1rem", fontSize: "0.9rem" }, children: ["Upload a CSV file with an ", _jsx("code", { children: "email" }), " column. Max 1,000 rows, 2 MB."] }), !jobId && (_jsxs("form", { onSubmit: handleUpload, style: { display: "flex", gap: "0.5rem", flexWrap: "wrap" }, children: [_jsx("input", { ref: fileRef, type: "file", accept: ".csv,text/csv", required: true, style: { flex: 1, color: "#e8e8e8" } }), _jsx("button", { type: "submit", style: {
                            padding: "0.6rem 1.5rem",
                            borderRadius: "6px",
                            border: "none",
                            background: "#3b82f6",
                            color: "#fff",
                            fontWeight: 700,
                            cursor: "pointer",
                        }, children: "Upload & Validate" })] })), submitError && (_jsxs("p", { style: { color: "#ef4444", marginTop: "1rem" }, children: ["Error: ", submitError] })), pollError && (_jsxs("p", { style: { color: "#ef4444", marginTop: "1rem" }, children: ["Poll error: ", pollError] })), meta && (_jsxs("div", { style: { marginTop: "1.5rem" }, children: [_jsxs("div", { style: { display: "flex", alignItems: "center", gap: "1rem" }, children: [_jsxs("span", { style: { fontWeight: 700 }, children: ["Status: ", _jsx("span", { style: { textTransform: "uppercase" }, children: meta.status })] }), (meta.status === "ready" || meta.status === "failed") && (_jsx("button", { onClick: handleDelete, disabled: deleting, style: {
                                    padding: "0.3rem 0.75rem",
                                    borderRadius: "6px",
                                    border: "1px solid #555",
                                    background: "transparent",
                                    color: "#ef4444",
                                    cursor: "pointer",
                                    fontSize: "0.85rem",
                                }, children: deleting ? "Deleting…" : "Delete Results" })), meta.status === "ready" && jobId && jobKey && (_jsx("a", { href: `/api/jobs/${jobId}/download`, download: true, style: { color: "#3b82f6", fontSize: "0.85rem" }, onClick: (e) => {
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
                                }, children: "\u2B07 Download CSV" }))] }), (meta.status === "pending" || meta.status === "running") && (_jsx(ProgressBar, { done: meta.done, total: meta.total })), meta.status === "failed" && (_jsxs("p", { style: { color: "#ef4444", marginTop: "1rem" }, children: ["Job failed: ", meta.error ?? "Unknown error"] })), meta.status === "ready" && jobId && jobKey && (_jsx(ResultsTable, { jobId: jobId, jobKey: jobKey, total: meta.total }))] }))] }));
}
