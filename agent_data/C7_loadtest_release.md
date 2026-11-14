# C7 — Load Test, Docs & Release
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Sonnet 4.6 Thinking**
**Prerequisite: C6 exit gate fully green AND the app is live on Render.**

---

## PROMPT (copy everything below this line)

---

You are a senior QA and release engineer. We are building **MailCheck**. This is **Chunk 7 – Load Test, Docs & Release**: write Locust load tests, generate a simple API reference, run the load tests, verify all [verify] estimates, and produce a release checklist.

### What to build in this chunk

#### 1. Install Locust (dev dependency)

Add to `backend/pyproject.toml` under `[project.optional-dependencies] dev`:

```toml
"locust>=2.31",
```

Then run:

```powershell
cd P:\mail_validator\backend
pip install -e ".[dev]"
```

#### 2. Load test script — `backend/tests/locustfile.py`

```python
"""
MailCheck load tests.
Run against the LOCAL server for safety (not production, to avoid rate limits).

Usage:
    cd P:\mail_validator\backend
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &   # or start in another terminal
    locust -f tests/locustfile.py --host http://localhost:8000 --headless \
           -u 30 -r 5 -t 60s --only-summary
"""
import csv
import io
import random
import string
from locust import HttpUser, TaskSet, task, between, events

VALID_EMAILS = [
    "user@gmail.com",
    "alice@example.com",
    "bob@outlook.com",
    "carol@yahoo.com",
    "dave@hotmail.com",
]

DISPOSABLE_EMAILS = [
    "test@mailinator.com",
    "throw@yopmail.com",
    "trash@guerrillamail.com",
]

INVALID_EMAILS = [
    "notanemail",
    "@nodomain",
    "double@@at.com",
]

def make_csv_content(n: int = 10) -> bytes:
    rows = ["email"]
    for _ in range(n):
        choice = random.choice(VALID_EMAILS + DISPOSABLE_EMAILS + INVALID_EMAILS)
        rows.append(choice)
    return "\n".join(rows).encode()


class SingleCheckTasks(TaskSet):
    @task(8)
    def check_valid(self) -> None:
        email = random.choice(VALID_EMAILS)
        self.client.post(
            "/api/validations/single",
            json={"email": email},
            name="/api/validations/single [valid]",
        )

    @task(2)
    def check_disposable(self) -> None:
        email = random.choice(DISPOSABLE_EMAILS)
        self.client.post(
            "/api/validations/single",
            json={"email": email},
            name="/api/validations/single [disposable]",
        )

    @task(1)
    def check_invalid(self) -> None:
        email = random.choice(INVALID_EMAILS)
        self.client.post(
            "/api/validations/single",
            json={"email": email},
            name="/api/validations/single [invalid]",
        )

    @task(1)
    def health(self) -> None:
        self.client.get("/api/health", name="/api/health")


class BulkCheckTasks(TaskSet):
    _job_id: str | None = None
    _job_key: str | None = None

    @task
    def full_bulk_flow(self) -> None:
        # Upload
        csv_bytes = make_csv_content(10)
        with self.client.post(
            "/api/validations/bulk",
            files={"file": ("emails.csv", io.BytesIO(csv_bytes), "text/csv")},
            name="/api/validations/bulk",
            catch_response=True,
        ) as resp:
            if resp.status_code == 503:
                resp.success()   # queue full is expected under load
                return
            if resp.status_code != 200:
                resp.failure(f"Submit failed: {resp.status_code}")
                return
            data = resp.json()
            self._job_id = data.get("job_id")
            self._job_key = data.get("job_key")

        if not self._job_id or not self._job_key:
            return

        # Poll up to 15 times (30 seconds)
        for _ in range(15):
            import time; time.sleep(2)
            r = self.client.get(
                f"/api/jobs/{self._job_id}",
                headers={"X-Job-Key": self._job_key},
                name="/api/jobs/{id} [poll]",
            )
            if r.status_code != 200:
                return
            status = r.json().get("status")
            if status in ("ready", "failed"):
                break

        # Download
        if status == "ready":
            self.client.get(
                f"/api/jobs/{self._job_id}/download",
                headers={"X-Job-Key": self._job_key},
                name="/api/jobs/{id}/download",
            )

        # Delete
        self.client.delete(
            f"/api/jobs/{self._job_id}",
            headers={"X-Job-Key": self._job_key},
            name="/api/jobs/{id} [delete]",
        )


class SingleUser(HttpUser):
    tasks = [SingleCheckTasks]
    wait_time = between(1, 3)
    weight = 4   # 80% of users


class BulkUser(HttpUser):
    tasks = [BulkCheckTasks]
    wait_time = between(5, 15)
    weight = 1   # 20% of users
```

#### 3. Run the load test locally and record results

```powershell
# Terminal 1: start the app
cd P:\mail_validator\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: run locust headless
cd P:\mail_validator\backend
locust -f tests/locustfile.py --host http://localhost:8000 --headless `
       -u 30 -r 5 -t 90s --only-summary --csv loadtest_results
```

This writes `loadtest_results_stats.csv` and `loadtest_results_failures.csv`.

#### 4. Load test result verification script — `backend/tests/verify_loadtest.py`

```python
"""
Run after the Locust test completes.
Reads loadtest_results_stats.csv and checks our [verify] targets.

Usage:
    cd P:\mail_validator\backend
    python tests/verify_loadtest.py
"""
import csv
import sys

STATS_FILE = "loadtest_results_stats.csv"
TARGET_P95_SINGLE_MS = 5000   # under 5 seconds p95 for single check
TARGET_FAILURE_RATE = 0.05    # under 5% failures overall

def main() -> None:
    rows: list[dict] = []
    try:
        with open(STATS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"ERROR: {STATS_FILE} not found. Run locust first.")
        sys.exit(1)

    failures: list[str] = []

    for row in rows:
        name = row.get("Name", "")
        if "single" in name.lower() and "[valid]" in name:
            p95 = float(row.get("95%", 0))
            if p95 > TARGET_P95_SINGLE_MS:
                failures.append(
                    f"FAIL: Single-check p95={p95:.0f}ms > {TARGET_P95_SINGLE_MS}ms target"
                )
            else:
                print(f"PASS: Single-check p95={p95:.0f}ms ≤ {TARGET_P95_SINGLE_MS}ms")

        req_count = int(row.get("Request Count", 0) or 0)
        fail_count = int(row.get("Failure Count", 0) or 0)
        if req_count > 0:
            rate = fail_count / req_count
            if rate > TARGET_FAILURE_RATE:
                failures.append(
                    f"FAIL: {name} failure rate={rate:.1%} > {TARGET_FAILURE_RATE:.0%}"
                )

    if failures:
        print("\nLoad test FAILED:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\nAll load test targets met. ✅")

if __name__ == "__main__":
    main()
```

Run it:

```powershell
cd P:\mail_validator\backend
python tests/verify_loadtest.py
```

#### 5. Memory usage check script — `backend/tests/check_memory.py`

```python
"""
Check peak memory during the load test.
Run on Linux (Render) or WSL2.

Usage:
    # In a separate terminal while locust is running:
    python tests/check_memory.py
"""
import time, os, sys

GUARD_MB = 380  # from settings

def read_rss_mb() -> float | None:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        return None
    return None

def main() -> None:
    peak = 0.0
    print("Monitoring memory for 90 seconds... (run locust in another terminal)")
    for _ in range(90):
        mb = read_rss_mb()
        if mb is not None:
            peak = max(peak, mb)
            print(f"  RSS: {mb:.1f} MB (peak: {peak:.1f} MB)", end="\r")
        time.sleep(1)
    print()
    if peak > GUARD_MB:
        print(f"FAIL: Peak RSS {peak:.1f} MB exceeds guard {GUARD_MB} MB")
        sys.exit(1)
    else:
        print(f"PASS: Peak RSS {peak:.1f} MB ≤ guard {GUARD_MB} MB ✅")

if __name__ == "__main__":
    main()
```

#### 6. `docs/API.md` — API reference

```markdown
# MailCheck API Reference

Base URL: `https://your-app.onrender.com/api`  
Interactive docs: `/api/docs` (OpenAPI / Swagger UI)

---

## Authentication

Bulk job endpoints require the `X-Job-Key` header.  
You receive this key from `POST /validations/bulk`. Store it; it is not recoverable.

---

## Endpoints

### GET /health

Health check. No auth.

**Response 200**
```json
{ "status": "ok", "ts": 1731579600 }
```

---

### POST /validations/single

Validate one email address. Limit: 20 requests/minute/IP.

**Request body**
```json
{ "email": "user@example.com" }
```

**Response 200**
```json
{
  "address": "user@example.com",
  "status": "valid",
  "is_disposable": false,
  "is_role": false,
  "domain": "example.com",
  "checks": {
    "syntax": "pass",
    "mx": "pass",
    "disposable": "pass",
    "role": "pass"
  }
}
```

**Status values:** `valid` | `risky` | `invalid` | `unknown`

**Check values:** `pass` | `fail` | `error` | `skip`

**Errors:** 429 `RATE_LIMITED`

---

### POST /validations/bulk

Upload a CSV file for bulk validation. Limit: 5 uploads/hour/IP.

**Request:** `multipart/form-data`, field name `file`, `.csv` file.  
CSV must have an `email` column (also accepts `e-mail`, `email address`).  
Max 2 MB, max 1,000 rows.

**Response 200**
```json
{
  "job_id": "3fa85f64-...",
  "job_key": "xK9mP2...",
  "total": 500,
  "status": "pending"
}
```

**Errors:** 422 `CSV_PARSE_ERROR` | `FILE_TOO_LARGE` | `INVALID_EMAIL_COLUMN`; 503 `QUEUE_FULL`

---

### GET /jobs/{job_id}

Poll job status. Header: `X-Job-Key: <key>`.

**Response 200**
```json
{
  "job_id": "3fa85f64-...",
  "status": "running",
  "total": 500,
  "done": 120,
  "error": null
}
```

**Errors:** 403 `JOB_ACCESS_DENIED` | 404 `JOB_NOT_FOUND`

---

### GET /jobs/{job_id}/results

Get paginated results. Only available when status is `ready`. Header: `X-Job-Key`.

**Query params:** `page` (default 1), `page_size` (default 100, max 500).

**Response 200**
```json
{
  "total": 500,
  "done": 500,
  "page": 1,
  "page_size": 100,
  "results": [
    {
      "address": "user@example.com",
      "status": "valid",
      "is_disposable": false,
      "is_role": false,
      "domain": "example.com",
      "checks": { "syntax": "pass", "mx": "pass", "disposable": "pass", "role": "pass" }
    }
  ]
}
```

**Errors:** 403 | 404 | 409 `JOB_NOT_READY`

---

### GET /jobs/{job_id}/download

Stream results as a CSV file. Repeatable until job expires. Header: `X-Job-Key`.

**Response:** `text/csv` with header row `address,status,is_disposable,is_role,domain`.

---

### DELETE /jobs/{job_id}

Delete a job and its results immediately. Header: `X-Job-Key`.

**Response 200**
```json
{ "deleted": true }
```

---

## Error envelope

All error responses use this structure:

```json
{
  "error": "Human-readable message",
  "code": "MACHINE_CODE",
  "detail": "Optional extra detail"
}
```

## Job retention

| Event | TTL |
|-------|-----|
| Job READY | 15 minutes after completion |
| Job FAILED | 60 seconds after failure |
| Any job (hard cap) | 30 minutes after creation |
```

---

### Release checklist

Create `docs/RELEASE_CHECKLIST.md`:

```markdown
# MailCheck Release Checklist

## Pre-release
- [ ] All C0 to C7 exit gates passed
- [ ] GitHub Actions CI: all three jobs green on `main`
- [ ] `ruff check backend/app backend/tests` → clean
- [ ] `mypy backend/app` → no errors
- [ ] `npm audit` → no high/critical vulnerabilities
- [ ] `pip-audit -r backend/requirements.txt` → no known vulnerabilities
- [ ] Load test: single-check p95 < 5 s under 30 simulated users [verify ✅ or ❌]
- [ ] Load test: failure rate < 5% [verify ✅ or ❌]
- [ ] Memory peak < 380 MB under load [verify ✅ or ❌]

## Deployment
- [ ] Render service: green (healthy)
- [ ] `GET /api/health` → 200
- [ ] Single check with `user@gmail.com` → result shown
- [ ] Upload 5-row CSV → results shown → download works → delete works
- [ ] Security headers present in browser DevTools (X-Content-Type-Options, CSP)
- [ ] No `Server` header in responses

## Documentation
- [ ] `README.md` reflects current stack and run instructions
- [ ] `docs/API.md` matches actual endpoint behaviour
- [ ] Open decisions resolved (retention window, custom domain)

## Done
- [ ] Git tag: `git tag -a v1.0.0 -m "Initial release"`
- [ ] Push tag: `git push origin v1.0.0`
```

---

### How to run all final tests

```powershell
# 1. Backend unit + integration tests
cd P:\mail_validator\backend
pytest tests/ -v --tb=short

# 2. Frontend
cd P:\mail_validator\frontend
npm test

# 3. Security audit
cd P:\mail_validator\backend
pip-audit

cd P:\mail_validator\frontend
npm audit

# 4. Load test (needs local server running)
# Terminal 1:
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Terminal 2:
locust -f tests/locustfile.py --host http://localhost:8000 --headless -u 30 -r 5 -t 90s --only-summary --csv loadtest_results

# 5. Verify load test results
python tests/verify_loadtest.py
```

---

### Exit gate for C7 (= Release gate)

- [ ] 30+ backend unit tests pass
- [ ] Frontend Vitest tests pass
- [ ] Load test: 30 simulated users, single-check p95 < 5000 ms (**fill in actual:** ___ ms)
- [ ] Load test: failure rate < 5% (**fill in actual:** ___%)
- [ ] `pip-audit` → no high/critical vulnerabilities
- [ ] `npm audit` → no high/critical vulnerabilities
- [ ] `docs/API.md` exists and is accurate
- [ ] `docs/RELEASE_CHECKLIST.md` all items ticked
- [ ] Git tag pushed: `v1.0.0`
- [ ] 🎉 **MailCheck is released!**
