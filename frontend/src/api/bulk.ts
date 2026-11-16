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

export function downloadUrl(jobId: string, _jobKey: string): string {
  return `/api/jobs/${jobId}/download`;
}
