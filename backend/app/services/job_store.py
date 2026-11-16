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
