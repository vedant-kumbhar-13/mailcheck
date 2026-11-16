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
