import csv
import io
import time
from typing import Annotated

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.api.ip import get_client_ip
from app.config import settings
from app.core.assessor import assess
from app.services import job_manager
from app.services.csv_service import CsvError, parse_csv
from app.services.job_store import store as job_store
from app.services.rate_limiter import RateLimiter, single_limiter

router = APIRouter()

# Bulk rate limiter: 5 uploads per hour per IP
bulk_limiter = RateLimiter(limit=settings.rate_bulk_per_hour, window_seconds=3600)


# ── Health ────────────────────────────────────────────────────────────────────


@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "ts": int(time.time())})


# ── Single check ──────────────────────────────────────────────────────────────


class SingleCheckRequest(BaseModel):
    email: str


@router.post("/validations/single")
async def single_check(body: SingleCheckRequest, request: Request) -> dict:
    ip = get_client_ip(request)
    if not single_limiter.hit(ip):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "code": "RATE_LIMITED",
                "detail": "Max 20 requests per minute per IP",
            },
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


# ── Bulk upload ───────────────────────────────────────────────────────────────


@router.post("/validations/bulk")
async def bulk_check(
    request: Request,
    file: Annotated[UploadFile, File()],
) -> dict:
    ip = get_client_ip(request)
    if not bulk_limiter.hit(ip):
        raise HTTPException(
            status_code=429,
            detail={"error": "Rate limited", "code": "RATE_LIMITED"},
        )
    try:
        emails = await parse_csv(file)
    except CsvError as e:
        raise HTTPException(422, detail={"error": e.detail, "code": e.code}) from e
    job, raw_key = await job_manager.submit(emails)
    return {
        "job_id": job.id,
        "job_key": raw_key,
        "total": job.total,
        "status": job.status.value,
    }


# ── Job status ────────────────────────────────────────────────────────────────


@router.get("/jobs/{job_id}")
async def job_status(
    job_id: str,
    x_job_key: str = Header(...),
) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    return {
        "job_id": job.id,
        "status": job.status.value,
        "total": job.total,
        "done": job.done,
        "error": job.error,
    }


# ── Job results (paginated) ───────────────────────────────────────────────────


@router.get("/jobs/{job_id}/results")
async def job_results(
    job_id: str,
    x_job_key: str = Header(...),
    page: int = 1,
    page_size: int = 100,
) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    if job.status.value not in ("ready",):
        raise HTTPException(409, detail={"error": "Not ready", "code": "JOB_NOT_READY"})
    return job_manager.get_page(job, page=page, page_size=max(1, min(page_size, 500)))


# ── Job CSV download ──────────────────────────────────────────────────────────

_UNSAFE_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(val: str) -> str:
    """Prefix formula-injection characters to prevent CSV injection."""
    return f"'{val}" if val.startswith(_UNSAFE_PREFIXES) else val


@router.get("/jobs/{job_id}/download")
async def job_download(
    job_id: str,
    x_job_key: str = Header(...),
) -> StreamingResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    if job.status != "ready":
        raise HTTPException(409, detail={"error": "Not ready", "code": "JOB_NOT_READY"})

    def generate():
        # Header row
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["address", "status", "is_disposable", "is_role", "domain"])
        yield buf.getvalue()
        # Data rows
        for row in job.results:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(
                [
                    _csv_safe(str(row.get("address", ""))),
                    _csv_safe(str(row.get("status", ""))),
                    str(row.get("is_disposable", "")),
                    str(row.get("is_role", "")),
                    _csv_safe(str(row.get("domain", ""))),
                ]
            )
            yield buf.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="mailcheck_{job_id[:8]}.csv"'},
    )


# ── Delete job ────────────────────────────────────────────────────────────────


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    x_job_key: str = Header(...),
) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "Not found", "code": "JOB_NOT_FOUND"})
    if not job_manager.authorize(job, x_job_key):
        raise HTTPException(403, detail={"error": "Access denied", "code": "JOB_ACCESS_DENIED"})
    job_store.delete(job_id)
    return {"deleted": True}
