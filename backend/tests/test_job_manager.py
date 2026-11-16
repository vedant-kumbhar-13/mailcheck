import asyncio
from unittest.mock import AsyncMock

import pytest

from app.core.models import EmailResult, EmailStatus, JobStatus
from app.services import job_manager
from app.services.job_store import store


@pytest.fixture(autouse=True)
def clean_store():
    store._jobs.clear()
    job_manager._waiting_count = 0
    # Also reset the running semaphore to its original value between tests
    # (re-create it so a previous test's lock doesn't bleed over)
    job_manager._running_sem = asyncio.Semaphore(2)
    yield
    store._jobs.clear()
    job_manager._waiting_count = 0


MOCK_RESULT = EmailResult(
    address="user@example.com",
    status=EmailStatus.VALID,
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
