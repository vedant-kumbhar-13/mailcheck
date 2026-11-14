"""
Top-level function: assess one email address.
Callers import only this module from core.
"""

from __future__ import annotations

from app.config import settings
from app.core.dns_resolver import resolve_domain
from app.core.lists import is_disposable, is_role_based
from app.core.models import DomainResult, EmailResult, EmailStatus
from app.core.syntax import check_syntax


async def assess(address: str) -> EmailResult:
    """
    Full assessment pipeline for one email address.
    Returns an EmailResult. Never raises.
    """
    checks: dict[str, str] = {}

    # 1. Syntax
    ok, normalised = check_syntax(address)
    checks["syntax"] = "pass" if ok else "fail"
    if not ok:
        return EmailResult(
            address=address,
            status=EmailStatus.INVALID,
            checks=checks,
        )

    local_part, domain = normalised.split("@", 1)

    # 2. DNS
    dr: DomainResult = await resolve_domain(domain, timeout=settings.dns_timeout_seconds)
    if dr.is_null_mx:
        checks["mx"] = "fail"
        return EmailResult(
            address=normalised, status=EmailStatus.INVALID, domain=domain, checks=checks
        )
    elif dr.dns_error:
        checks["mx"] = "error"
        return EmailResult(
            address=normalised, status=EmailStatus.UNKNOWN, domain=domain, checks=checks
        )
    else:
        checks["mx"] = "pass"

    # 3. Disposable
    disp = is_disposable(domain)
    checks["disposable"] = "fail" if disp else "pass"

    # 4. Role
    role = is_role_based(local_part)
    checks["role"] = "fail" if role else "pass"

    # 5. Score
    if disp or role:
        status = EmailStatus.RISKY
    else:
        status = EmailStatus.VALID

    return EmailResult(
        address=normalised,
        status=status,
        is_disposable=disp,
        is_role=role,
        domain=domain,
        checks=checks,
    )
