export async function submitBulk(file) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/validations/bulk", { method: "POST", body: form });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail?.error ?? `HTTP ${res.status}`);
    }
    return res.json();
}
export async function getJobStatus(jobId, jobKey) {
    const res = await fetch(`/api/jobs/${jobId}`, {
        headers: { "X-Job-Key": jobKey },
    });
    if (!res.ok)
        throw new Error(`HTTP ${res.status}`);
    return res.json();
}
export async function getResults(jobId, jobKey, page, pageSize = 100) {
    const res = await fetch(`/api/jobs/${jobId}/results?page=${page}&page_size=${pageSize}`, { headers: { "X-Job-Key": jobKey } });
    if (!res.ok)
        throw new Error(`HTTP ${res.status}`);
    return res.json();
}
export async function deleteJob(jobId, jobKey) {
    await fetch(`/api/jobs/${jobId}`, {
        method: "DELETE",
        headers: { "X-Job-Key": jobKey },
    });
}
export function downloadUrl(jobId, _jobKey) {
    return `/api/jobs/${jobId}/download`;
}
