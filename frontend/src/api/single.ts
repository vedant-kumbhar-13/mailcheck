export interface SingleResult {
  address: string;
  status: "valid" | "invalid" | "risky" | "unknown";
  is_disposable: boolean;
  is_role: boolean;
  domain: string;
  checks: Record<string, string>;
}

export async function checkSingle(email: string): Promise<SingleResult> {
  const res = await fetch("/api/validations/single", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.error ?? `HTTP ${res.status}`);
  }
  return res.json();
}
