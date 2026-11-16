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
            detail={
                "error": "Queue full",
                "code": "QUEUE_FULL",
                "detail": f"Max {settings.max_waiting_jobs} jobs waiting",
            },
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
                job.results.append(
                    {
                        "address": result.address,
                        "status": result.status.value,
                        "is_disposable": result.is_disposable,
                        "is_role": result.is_role,
                        "domain": result.domain,
                        "checks": result.checks,
                    }
                )
                job.done += 1

            await asyncio.gather(*[assess_one(e) for e in emails])
            job.status = JobStatus.READY
            job.finished_at = time.monotonic()

    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed: %s", job.id, exc)
        job.status = JobStatus.FAILED
        job.error = str(exc)[:200]
        job.finished_at = time.monotonic()


def get_page(job: Job, page: int = 1, page_size: int = 100) -> dict[str, object]:
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
