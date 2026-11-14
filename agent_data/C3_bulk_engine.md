# C3 — Bulk Engine
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Opus 4.6 Thinking** ← use Opus for this one; it has complex async logic
**Prerequisite: C1 exit gate fully green (C2 not required).**

---

## PROMPT (copy everything below this line)

---

You are a senior Python engineer specialising in async concurrency. We are building **MailCheck**. This is **Chunk 3 – Bulk Engine**: add CSV upload, in-process async job processing, job state machine, job store, and all bulk API endpoints. No React UI yet (that is C4).

### Concurrency model

```
POST /validations/bulk
  │
  ▼
csv_service.parse()          # streaming parse, 2 MB / 1000-row cap
  │
  ▼
job_manager.submit()
  │  semaphore: 2 running, 3 waiting
  ▼
asyncio.create_task(_run(job))
  │
  ├── semaphore acquired → status RUNNING
  │     for each email (semaphore: 20 DNS in flight)
  │       assessor.assess(email)
  │     status READY
  │
  └── semaphore timeout / queue full → status FAILED

Sweeper asyncio.Task (every 30 s):
  for each job:
    if READY and age > TTL (900 s)  → delete
    if FAILED and age > 60 s        → delete
    if any status and age > 1800 s  → delete
```

### Job state machine

```
PENDING → RUNNING → READY
         ↘        ↗
          FAILED
```

A job can never go backwards. READY and FAILED are terminal.

### Files to create / modify

#### 1. `backend/app/core/models.py` — extend with Job model

Add these classes to the existing file (keep everything already there):

```python
from enum import Enum
import time, uuid, secrets, hashlib
from dataclasses import dataclass, field
from typing import Any

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"

@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key_hash: str = ""         # SHA-256 of the raw job key
    status: JobStatus = JobStatus.PENDING
    total: int = 0
    done: int = 0
    error: str | None = None
    results: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None

    @staticmethod
    def new(total: int) -> tuple["Job", str]:
        """Create a new job and return (job, raw_key)."""
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        job = Job(total=total, key_hash=key_hash)
        return job, raw_key
```

#### 2. `backend/app/services/job_store.py`

```python
"""
In-memory job store. No persistence — jobs are lost on restart.
Thread-safe for asyncio (single event loop, no threads).
"""
from __future__ import annotations
from app.core.models import Job

class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def put(self, job: Job) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    def all_jobs(self) -> list[Job]:
        return list(self._jobs.values())

# Singleton
store = JobStore()
```

#### 3. `backend/app/services/csv_service.py`

```python
"""
CSV parsing with hardened constraints.
- Streaming read up to MAX_CSV_BYTES.
- Max MAX_CSV_ROWS data rows.
- UTF-8 with optional BOM.
- Binary content rejection.
- Strict csv.reader parsing.
- Returns list of raw email strings (not yet validated).
"""
from __future__ import annotations
import csv
import io
from fastapi import UploadFile, HTTPException
from app.config import settings

class CsvError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

async def parse_csv(file: UploadFile) -> list[str]:
    """
    Parse uploaded CSV. Returns a list of raw email strings.
    Raises CsvError on any structural problem.
    """
    # 1. Read up to MAX_CSV_BYTES + 1 (to detect over-limit)
    raw = await file.read(settings.max_csv_bytes + 1)
    if len(raw) > settings.max_csv_bytes:
        raise CsvError("FILE_TOO_LARGE", f"File exceeds {settings.max_csv_bytes} bytes")

    # 2. Reject binary content (null bytes)
    if b"\x00" in raw:
        raise CsvError("CSV_PARSE_ERROR", "Binary content detected")

    # 3. Decode UTF-8 with BOM
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise CsvError("CSV_PARSE_ERROR", f"Encoding error: {e}") from e

    # 4. Parse CSV
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise CsvError("CSV_PARSE_ERROR", "Empty file")

    # 5. Find email column
    headers = [h.strip().lower() for h in rows[0]]
    email_col: int | None = None
    for candidate in ("email", "email address", "e-mail", "emailaddress"):
        if candidate in headers:
            email_col = headers.index(candidate)
            break
    if email_col is None:
        # Try first column as fallback if no header looks like email
        # but only if the first row looks like a header (non-email value)
        from app.core.syntax import check_syntax
        ok, _ = check_syntax(rows[0][0].strip() if rows[0] else "")
        if ok:
            # First row is actual data, no header; treat col 0 as emails
            email_col = 0
            data_rows = rows
        else:
            raise CsvError(
                "INVALID_EMAIL_COLUMN",
                "Could not find an 'email' column. "
                "Please name your column: email, e-mail, or email address.",
            )
    else:
        data_rows = rows[1:]  # skip header row

    # 6. Extract emails, enforce row limit
    emails: list[str] = []
    for row in data_rows:
        if len(emails) >= settings.max_csv_rows:
            break
        if len(row) > email_col:
            val = row[email_col].strip()
            if val:
                emails.append(val)

    if not emails:
        raise CsvError("CSV_PARSE_ERROR", "No email addresses found in file")

    return emails
```

#### 4. `backend/app/services/job_manager.py`

```python
"""
Manages job lifecycle: submit, run, authorize, status, page results, delete.
"""
from __future__ import annotations
import asyncio
import hashlib
import hmac
import logging
import time
from app.config import settings
from app.core.assessor import assess
from app.core.models import Job, JobStatus
from app.services.job_store import store

logger = logging.getLogger(__name__)

# Concurrency controls
_running_sem = asyncio.Semaphore(settings.max_running_jobs)
_waiting_count: int = 0

def authorize(job: Job, raw_key: str) -> bool:
    """Compare key with stored hash using constant-time comparison."""
    expected = hashlib.sha256(raw_key.encode()).hexdigest()
    return hmac.compare_digest(expected, job.key_hash)

async def submit(emails: list[str]) -> tuple[Job, str]:
    """
    Create a new job and schedule it.
    Returns (job, raw_key).
    Raises HTTPException 503 if queue is full.
    """
    global _waiting_count
    from fastapi import HTTPException

    if _waiting_count >= settings.max_waiting_jobs:
        raise HTTPException(
            status_code=503,
            detail={"error": "Queue full", "code": "QUEUE_FULL",
                    "detail": f"Max {settings.max_waiting_jobs} jobs waiting"},
        )

    job, raw_key = Job.new(total=len(emails))
    store.put(job)
    _waiting_count += 1
    asyncio.create_task(_run(job, emails))
    return job, raw_key

async def _run(job: Job, emails: list[str]) -> None:
    """Main job coroutine. Runs inside a semaphore."""
    global _waiting_count
    _waiting_count = max(0, _waiting_count - 1)

    try:
        async with _running_sem:
            # Hard cap: fail if started too late
            age = time.monotonic() - job.created_at
            if age > settings.max_job_lifetime_seconds:
                job.status = JobStatus.FAILED
                job.error = "Job expired before it could start"
                job.finished_at = time.monotonic()
                return

            job.status = JobStatus.RUNNING
            dns_sem = asyncio.Semaphore(settings.dns_concurrency)

            async def assess_one(email: str) -> None:
                async with dns_sem:
                    result = await assess(email)
                job.results.append({
                    "address": result.address,
                    "status": result.status.value,
                    "is_disposable": result.is_disposable,
                    "is_role": result.is_role,
                    "domain": result.domain,
                    "checks": result.checks,
                })
                job.done += 1

            await asyncio.gather(*[assess_one(e) for e in emails])
            job.status = JobStatus.READY
            job.finished_at = time.monotonic()

    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed: %s", job.id, exc)
        job.status = JobStatus.FAILED
        job.error = str(exc)[:200]
        job.finished_at = time.monotonic()

def get_page(job: Job, page: int = 1, page_size: int = 100) -> dict:
    """Return a paginated slice of results."""
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "total": job.total,
        "done": job.done,
        "page": page,
        "page_size": page_size,
        "results": job.results[start:end],
    }
```

#### 5. `backend/app/services/sweeper.py`

```python
"""
Background task: delete expired jobs every 30 seconds.
"""
from __future__ import annotations
import asyncio
import logging
import time
from app.config import settings
from app.core.models import JobStatus
from app.services.job_store import store

logger = logging.getLogger(__name__)

async def sweep_loop() -> None:
    while True:
        await asyncio.sleep(30)
        _sweep_once()

def _sweep_once() -> None:
    now = time.monotonic()
    for job in store.all_jobs():
        age = now - job.created_at
        # Hard cap
        if age > settings.max_job_lifetime_seconds:
            logger.info("Sweeper: deleting job %s (hard cap)", job.id)
            store.delete(job.id)
            continue
        if job.status == JobStatus.READY and job.finished_at:
            if now - job.finished_at > settings.job_result_ttl_seconds:
                logger.info("Sweeper: deleting job %s (ready TTL)", job.id)
                store.delete(job.id)
        elif job.status == JobStatus.FAILED and job.finished_at:
            if now - job.finished_at > settings.failed_job_ttl_seconds:
                logger.info("Sweeper: deleting job %s (failed TTL)", job.id)
                store.delete(job.id)
```

#### 6. `backend/app/main.py` — add sweeper startup

```python
# Add to the existing startup handler:
from app.services.sweeper import sweep_loop

@app.on_event("startup")
async def startup() -> None:
    logger.info("MailCheck starting up")
    asyncio.create_task(sweep_loop())   # ← add this line
```

#### 7. Bulk API routes — add to `backend/app/api/routes.py`

```python
# Additional imports
import csv, io
from fastapi import UploadFile, File, Header
from app.services import job_manager
from app.services.csv_service import parse_csv, CsvError
from app.services.job_store import store as job_store
from app.services.rate_limiter import RateLimiter
from app.config import settings

bulk_limiter = RateLimiter(limit=settings.rate_bulk_per_hour, window_seconds=3600)

@router.post("/validations/bulk")
async def bulk_check(file: UploadFile = File(...), request: Request = None) -> dict:
    ip = get_client_ip(request)
    if not bulk_limiter.hit(ip):
        raise HTTPException(429, detail={"error": "Rate limited", "code": "RATE_LIMITED"})
    try:
        emails = await parse_csv(file)
    except CsvError as e:
        raise HTTPException(422, detail={"error": e.detail, "code": e.code}) from e
    job, raw_key = await job_manager.submit(emails)
    return {"job_id": job.id, "job_key": raw_key, "total": job.total, "status": job.status.value}

@router.get("/jobs/{job_id}")
async def job_status(job_id: str, x_job_key: str = Header(...)) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    return {"job_id": job.id, "status": job.status.value, "total": job.total,
            "done": job.done, "error": job.error}

@router.get("/jobs/{job_id}/results")
async def job_results(
    job_id: str, x_job_key: str = Header(...), page: int = 1, page_size: int = 100
) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    if job.status.value not in ("ready",):
        raise HTTPException(409, detail={"error": "Not ready", "code": "JOB_NOT_READY"})
    return job_manager.get_page(job, page=page, page_size=max(1, min(page_size, 500)))

@router.get("/jobs/{job_id}/download")
async def job_download(job_id: str, x_job_key: str = Header(...)):
    from fastapi.responses import StreamingResponse
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    if job.status != "ready":
        raise HTTPException(409, detail={"error": "Not ready", "code": "JOB_NOT_READY"})

    SAFE_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

    def _safe(val: str) -> str:
        """Prefix formula-injection characters."""
        return f"'{val}" if val.startswith(SAFE_PREFIXES) else val

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["address", "status", "is_disposable", "is_role", "domain"])
        yield output.getvalue()
        for row in job.results:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                _safe(str(row.get("address", ""))),
                _safe(str(row.get("status", ""))),
                str(row.get("is_disposable", "")),
                str(row.get("is_role", "")),
                _safe(str(row.get("domain", ""))),
            ])
            yield output.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="mailcheck_{job_id[:8]}.csv"'},
    )

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, x_job_key: str = Header(...)) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    job_store.delete(job_id)
    return {"deleted": True}
```

---

### Tests to create

#### `backend/tests/test_csv_service.py`

```python
import pytest
from io import BytesIO
from fastapi import UploadFile
from app.services.csv_service import parse_csv, CsvError

def make_upload(content: bytes, filename: str = "test.csv") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))

@pytest.mark.asyncio
async def test_valid_csv_with_header() -> None:
    csv = b"email\nuser@example.com\nadmin@test.org\n"
    result = await parse_csv(make_upload(csv))
    assert "user@example.com" in result
    assert "admin@test.org" in result

@pytest.mark.asyncio
async def test_csv_too_large() -> None:
    big = b"email\n" + b"a@b.com\n" * 400_000
    with pytest.raises(CsvError) as exc:
        await parse_csv(make_upload(big))
    assert exc.value.code == "FILE_TOO_LARGE"

@pytest.mark.asyncio
async def test_csv_binary_rejection() -> None:
    csv = b"email\nuser@example.com\x00binary"
    with pytest.raises(CsvError) as exc:
        await parse_csv(make_upload(csv))
    assert exc.value.code == "CSV_PARSE_ERROR"

@pytest.mark.asyncio
async def test_csv_no_email_column() -> None:
    csv = b"name,phone\nAlice,555-1234\n"
    with pytest.raises(CsvError) as exc:
        await parse_csv(make_upload(csv))
    assert exc.value.code == "INVALID_EMAIL_COLUMN"
```

#### `backend/tests/test_job_manager.py`

```python
import pytest, asyncio
from unittest.mock import AsyncMock, patch
from app.services import job_manager
from app.services.job_store import store
from app.core.models import JobStatus, EmailResult, EmailStatus, DomainResult

@pytest.fixture(autouse=True)
def clean_store():
    store._jobs.clear()
    job_manager._waiting_count = 0
    yield
    store._jobs.clear()
    job_manager._waiting_count = 0

MOCK_RESULT = EmailResult(
    address="user@example.com", status=EmailStatus.VALID,
    domain="example.com",
    checks={"syntax": "pass", "mx": "pass", "disposable": "pass", "role": "pass"},
)

@pytest.mark.asyncio
async def test_submit_and_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.job_manager.assess", AsyncMock(return_value=MOCK_RESULT))
    job, key = await job_manager.submit(["user@example.com"])
    assert store.get(job.id) is not None
    # Let the task run
    await asyncio.sleep(0.5)
    assert job.status == JobStatus.READY
    assert len(job.results) == 1

@pytest.mark.asyncio
async def test_authorize_valid_key() -> None:
    job, key = await job_manager.submit(["a@b.com"])
    assert job_manager.authorize(job, key) is True

@pytest.mark.asyncio
async def test_authorize_wrong_key() -> None:
    job, _ = await job_manager.submit(["a@b.com"])
    assert job_manager.authorize(job, "wrongkey") is False
```

#### `backend/tests/test_sweeper.py`

```python
import pytest, time
from app.services.sweeper import _sweep_once
from app.services.job_store import store
from app.core.models import Job, JobStatus
from app.config import settings

@pytest.fixture(autouse=True)
def clean():
    store._jobs.clear()
    yield
    store._jobs.clear()

def test_sweeper_removes_expired_ready_job() -> None:
    job, _ = Job.new(total=1)
    job.status = JobStatus.READY
    job.finished_at = time.monotonic() - settings.job_result_ttl_seconds - 1
    store.put(job)
    _sweep_once()
    assert store.get(job.id) is None

def test_sweeper_keeps_fresh_job() -> None:
    job, _ = Job.new(total=1)
    job.status = JobStatus.READY
    job.finished_at = time.monotonic()
    store.put(job)
    _sweep_once()
    assert store.get(job.id) is not None
```

---

### How to run tests

```powershell
cd P:\mail_validator\backend
pytest tests/ -v
```

**Expected:**

```
25+ passed, 0 failed
```

---

### Exit gate for C3

- [ ] 25+ tests pass
- [ ] `POST /api/validations/bulk` with a valid 5-row CSV → returns `job_id` and `job_key`
- [ ] `GET /api/jobs/{id}` with correct key → returns status
- [ ] `GET /api/jobs/{id}` with wrong key → 403
- [ ] `GET /api/jobs/{id}/results` when READY → returns paginated rows
- [ ] `GET /api/jobs/{id}/download` → downloads a `.csv` file
- [ ] `DELETE /api/jobs/{id}` → job removed from store
- [ ] Git commit: `git commit -m "C3: bulk engine – job store, CSV service, job manager, sweeper"`
