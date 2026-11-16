import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings
from app.services.sweeper import sweep_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MailCheck API", version="0.1.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins.split(","),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Job-Key"],
)

app.include_router(router, prefix="/api")

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.on_event("startup")
async def startup() -> None:
    logger.info("MailCheck starting up")
    asyncio.create_task(sweep_loop())
