from unittest.mock import AsyncMock

import pytest

from app.core.assessor import assess
from app.core.models import DomainResult, EmailStatus


@pytest.mark.asyncio
async def test_invalid_syntax() -> None:
    result = await assess("notanemail")
    assert result.status == EmailStatus.INVALID
    assert result.checks["syntax"] == "fail"


@pytest.mark.asyncio
async def test_valid_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.assessor.resolve_domain",
        AsyncMock(return_value=DomainResult(has_mx=True)),
    )
    result = await assess("user@example.com")
    assert result.status == EmailStatus.VALID


@pytest.mark.asyncio
async def test_disposable_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.assessor.resolve_domain",
        AsyncMock(return_value=DomainResult(has_mx=True)),
    )
    result = await assess("user@mailinator.com")
    assert result.status == EmailStatus.RISKY
    assert result.is_disposable is True


@pytest.mark.asyncio
async def test_role_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.assessor.resolve_domain",
        AsyncMock(return_value=DomainResult(has_mx=True)),
    )
    result = await assess("admin@example.com")
    assert result.status == EmailStatus.RISKY
    assert result.is_role is True


@pytest.mark.asyncio
async def test_dns_timeout_gives_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.assessor.resolve_domain",
        AsyncMock(return_value=DomainResult(dns_error="timeout")),
    )
    result = await assess("user@example.com")
    assert result.status == EmailStatus.UNKNOWN  # NEVER invalid


@pytest.mark.asyncio
async def test_null_mx_gives_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.assessor.resolve_domain",
        AsyncMock(return_value=DomainResult(is_null_mx=True)),
    )
    result = await assess("user@null-mx-domain.com")
    assert result.status == EmailStatus.INVALID
