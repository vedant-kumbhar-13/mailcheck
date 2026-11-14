import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "ts": int(time.time())})
