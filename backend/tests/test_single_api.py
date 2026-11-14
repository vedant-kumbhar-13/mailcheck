from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.models import EmailResult, EmailStatus
from app.main import app

MOCK_VALID = EmailResult(
    address="user@example.com",
    status=EmailStatus.VALID,
    domain="example.com",
    checks={"syntax": "pass", "mx": "pass", "disposable": "pass", "role": "pass"},
)


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Clear rate-limiter buckets before each test."""
    from app.services.rate_limiter import single_limiter

    single_limiter._buckets.clear()


@pytest.mark.asyncio
async def test_single_check_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.routes.assess", AsyncMock(return_value=MOCK_VALID))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/validations/single", json={"email": "user@example.com"})
    assert r.status_code == 200
    assert r.json()["status"] == "valid"


@pytest.mark.asyncio
async def test_single_check_rate_limited() -> None:
    from app.services.rate_limiter import single_limiter

    # Fill the bucket
    for _ in range(single_limiter._limit):
        single_limiter.hit("1.2.3.4")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/validations/single",
            json={"email": "x@x.com"},
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_single_check_missing_email() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/validations/single", json={})
    assert r.status_code == 422
