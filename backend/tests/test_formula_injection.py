import pytest
from httpx import ASGITransport, AsyncClient

from app.core.models import Job, JobStatus
from app.main import app


@pytest.mark.asyncio
async def test_formula_prefix_in_download() -> None:
    """CSV download must prefix formula-injection characters with '."""
    from app.services.job_store import store

    job, key = Job.new(total=1)
    job.status = JobStatus.READY
    job.results = [
        {
            "address": "=HYPERLINK(malicious)",
            "status": "valid",
            "is_disposable": False,
            "is_role": False,
            "domain": "x.com",
            "checks": {},
        }
    ]
    store.put(job)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"/api/jobs/{job.id}/download", headers={"X-Job-Key": key})

    store.delete(job.id)
    text = r.text
    assert "'=HYPERLINK" in text, "Formula injection not escaped"
