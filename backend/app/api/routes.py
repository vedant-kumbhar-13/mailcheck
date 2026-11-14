import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.ip import get_client_ip
from app.core.assessor import assess
from app.services.rate_limiter import single_limiter

router = APIRouter()


@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "ts": int(time.time())})


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
