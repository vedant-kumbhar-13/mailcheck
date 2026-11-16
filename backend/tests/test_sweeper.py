import time

import pytest

from app.config import settings
from app.core.models import Job, JobStatus
from app.services.job_store import store
from app.services.sweeper import _sweep_once


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
