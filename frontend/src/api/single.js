export async function checkSingle(email) {
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
