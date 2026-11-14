# C2 — Single-Check API + UI
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Sonnet 4.6 Thinking**
**Prerequisite: C1 exit gate fully green.**

---

## PROMPT (copy everything below this line)

---

You are a senior Python and TypeScript engineer. We are building **MailCheck**. This is **Chunk 2 – Single-Check API + UI**: add the `POST /api/validations/single` endpoint and the React UI for it.

### What already exists

- `backend/app/core/` — full validation logic (assessor, syntax, DNS, lists)
- `backend/app/api/routes.py` — only has `/health`
- `frontend/src/App.tsx` — placeholder

### What to build in this chunk

#### Back-end changes

**A. In-memory rate limiter** — `backend/app/services/rate_limiter.py`

```python
"""
Per-IP sliding-window rate limiter, stored in process memory.
No Redis. Thread-safe for asyncio (single-threaded event loop).
"""
from __future__ import annotations
import hashlib
import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def _key(self, raw_ip: str) -> str:
        """Hash the IP so we don't store PII in memory."""
        return hashlib.sha256(raw_ip.encode()).hexdigest()[:16]

    def hit(self, raw_ip: str) -> bool:
        """
        Returns True if the request is allowed, False if rate-limited.
        Records the hit only when allowed.
        """
        key = self._key(raw_ip)
        now = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - self._window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._limit:
            return False
        bucket.append(now)
        return True

# Singletons — created once at import time
from app.config import settings
single_limiter = RateLimiter(limit=settings.rate_single_per_min, window_seconds=60)
```

**B. IP helper** — `backend/app/api/ip.py`

```python
from fastapi import Request

def get_client_ip(request: Request) -> str:
    """
    Read the rightmost IP from X-Forwarded-For (last hop only).
    Falls back to request.client.host.
    """
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"
```

**C. Single-check endpoint** — extend `backend/app/api/routes.py`

```python
# Add these imports at the top of routes.py
from fastapi import Request, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.assessor import assess
from app.services.rate_limiter import single_limiter
from app.api.ip import get_client_ip

class SingleCheckRequest(BaseModel):
    email: str

@router.post("/validations/single")
async def single_check(body: SingleCheckRequest, request: Request) -> dict:
    ip = get_client_ip(request)
    if not single_limiter.hit(ip):
        raise HTTPException(
            status_code=429,
            detail={"error": "Rate limit exceeded", "code": "RATE_LIMITED",
                    "detail": "Max 20 requests per minute per IP"}
        )
    result = await assess(body.email)
    return {
        "address": result.address,
        "status": result.status.value,
        "is_disposable": result.is_disposable,
        "is_role": result.is_role,
        "domain": result.domain,
        "checks": result.checks,
    }
```

#### Front-end changes

Replace the placeholder `App.tsx` with the full single-check UI.

**`frontend/src/api/single.ts`**

```typescript
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
```

**`frontend/src/components/StatusBadge.tsx`**

```tsx
import type { SingleResult } from "../api/single";

const COLORS: Record<SingleResult["status"], string> = {
  valid: "#22c55e",
  risky: "#f59e0b",
  invalid: "#ef4444",
  unknown: "#94a3b8",
};

export function StatusBadge({ status }: { status: SingleResult["status"] }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.25rem 0.75rem",
        borderRadius: "9999px",
        background: COLORS[status],
        color: "#fff",
        fontWeight: 700,
        fontSize: "0.85rem",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      {status}
    </span>
  );
}
```

**`frontend/src/components/ChecksTable.tsx`**

```tsx
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
```

**`frontend/src/pages/SingleCheck.tsx`**

```tsx
import { useState, useRef } from "react";
import { checkSingle, type SingleResult } from "../api/single";
import { StatusBadge } from "../components/StatusBadge";
import { ChecksTable } from "../components/ChecksTable";

export function SingleCheck() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<SingleResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await checkSingle(email.trim());
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2 style={{ marginBottom: "1rem" }}>Single Email Check</h2>
      <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <input
          ref={inputRef}
          type="text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="user@example.com"
          required
          style={{
            flex: 1,
            minWidth: "16rem",
            padding: "0.6rem 1rem",
            borderRadius: "6px",
            border: "1px solid #333",
            background: "#1a1a1a",
            color: "#e8e8e8",
            fontSize: "1rem",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "0.6rem 1.5rem",
            borderRadius: "6px",
            border: "none",
            background: "#3b82f6",
            color: "#fff",
            fontWeight: 700,
            cursor: loading ? "wait" : "pointer",
            fontSize: "1rem",
          }}
        >
          {loading ? "Checking…" : "Check"}
        </button>
      </form>

      {error && (
        <p style={{ marginTop: "1rem", color: "#ef4444" }}>Error: {error}</p>
      )}

      {result && (
        <div style={{ marginTop: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span style={{ fontSize: "0.9rem", color: "#aaa" }}>{result.address}</span>
            <StatusBadge status={result.status} />
          </div>
          <ChecksTable checks={result.checks} />
        </div>
      )}
    </section>
  );
}
```

**`frontend/src/App.tsx`** (replace entirely)

```tsx
import { SingleCheck } from "./pages/SingleCheck";

export default function App() {
  return (
    <main className="app">
      <header style={{ marginBottom: "2rem" }}>
        <h1>MailCheck</h1>
        <p style={{ color: "#888", marginTop: "0.25rem" }}>Privacy-first email validation</p>
      </header>
      <SingleCheck />
    </main>
  );
}
```

---

### Tests to create

#### `backend/tests/test_single_api.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.models import EmailResult, EmailStatus, DomainResult

MOCK_VALID = EmailResult(
    address="user@example.com",
    status=EmailStatus.VALID,
    domain="example.com",
    checks={"syntax": "pass", "mx": "pass", "disposable": "pass", "role": "pass"},
)

@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Clear rate-limiter buckets before each test."""
    from app.services.rate_limiter import single_limiter
    single_limiter._buckets.clear()

@pytest.mark.asyncio
async def test_single_check_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.routes.assess", AsyncMock(return_value=MOCK_VALID))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/validations/single", json={"email": "user@example.com"})
    assert r.status_code == 200
    assert r.json()["status"] == "valid"

@pytest.mark.asyncio
async def test_single_check_rate_limited() -> None:
    from app.services.rate_limiter import single_limiter
    # Fill the bucket
    for _ in range(single_limiter._limit):
        single_limiter.hit("1.2.3.4")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/validations/single",
            json={"email": "x@x.com"},
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
    assert r.status_code == 429

@pytest.mark.asyncio
async def test_single_check_missing_email() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/validations/single", json={})
    assert r.status_code == 422
```

#### `frontend/src/components/StatusBadge.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

test("renders valid badge", () => {
  render(<StatusBadge status="valid" />);
  expect(screen.getByText("valid")).toBeTruthy();
});

test("renders invalid badge", () => {
  render(<StatusBadge status="invalid" />);
  expect(screen.getByText("invalid")).toBeTruthy();
});
```

---

### How to run tests

```powershell
# Backend
cd P:\mail_validator\backend
pytest tests/ -v

# Frontend
cd P:\mail_validator\frontend
npm test
```

**Expected:**

```
# Backend
17+ passed, 0 failed

# Frontend
✓ StatusBadge > renders valid badge
✓ StatusBadge > renders invalid badge
2 passed
```

**Manual check:** Open `http://localhost:5173`, type `admin@mailinator.com`, click Check.
Expected result: status badge shows `risky`, checks table shows disposable: ❌, role: ❌.

---

### Exit gate for C2

- [ ] All backend tests pass (17+)
- [ ] Frontend Vitest passes (2+)
- [ ] Manual check: `user@gmail.com` → `valid` or `unknown`
- [ ] Manual check: `admin@mailinator.com` → `risky`
- [ ] Manual check: `notanemail` → `invalid`
- [ ] Rate limiter: submit 21 times fast → 21st returns 429
- [ ] Git commit: `git commit -m "C2: single-check endpoint and React UI"`
