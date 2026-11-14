# C1 — Validation Core
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Sonnet 4.6 Thinking**
**Prerequisite: C0 exit gate is fully green.**

---

## PROMPT (copy everything below this line)

---

You are a senior Python engineer. We are building **MailCheck**, a privacy-first email validation web app. This is **Chunk 1 – Validation Core**: implement all validation logic (syntax, DNS/MX, disposable, role-based, scoring) with no HTTP exposure yet. This logic lives entirely in `backend/app/core/`.

### Rules for this chunk

- Do **not** create any FastAPI routes. That is C2.
- Do **not** import anything from `app.api` or `app.services`.
- `core/` must have zero imports from `api/` or `services/`. Layering: `api → services → core`, never reversed.
- DNS failures → result status `unknown`, **never** `invalid`. This is a hard rule.
- Use `dnspython`'s async resolver (not the sync one).
- Use `email_validator.validate_email()` with `check_deliverability=False` for syntax only.
- No external HTTP calls. No SMTP probing.

### Result status values

| Status | Meaning |
|--------|---------|
| `valid` | Syntax OK, MX or A/AAAA record found, not disposable, not role |
| `risky` | Syntax OK, DNS OK, but disposable OR role-based |
| `invalid` | Syntax fails OR explicit Null MX record (RFC 7505 `0 .`) |
| `unknown` | Syntax OK, DNS lookup failed (timeout, NXDOMAIN, SERVFAIL, etc.) |

### Files to create

#### 1. `backend/app/core/models.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class EmailStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    RISKY = "risky"
    UNKNOWN = "unknown"

@dataclass
class DomainResult:
    """Raw DNS findings for a domain."""
    has_mx: bool = False
    has_a_aaaa: bool = False
    is_null_mx: bool = False   # RFC 7505: "0 ." record
    dns_error: str | None = None   # set when lookup failed

@dataclass
class EmailResult:
    """Full assessment result for one email address."""
    address: str
    status: EmailStatus
    is_disposable: bool = False
    is_role: bool = False
    domain: str = ""
    checks: dict[str, str] = field(default_factory=dict)
    # checks keys: syntax, mx, disposable, role
    # checks values: "pass" | "fail" | "skip" | "error"
```

#### 2. `backend/app/core/syntax.py`

```python
from email_validator import validate_email, EmailNotValidError

def check_syntax(address: str) -> tuple[bool, str]:
    """
    Returns (is_valid, normalized_or_original).
    Uses email-validator with check_deliverability=False.
    """
    try:
        info = validate_email(address, check_deliverability=False)
        return True, info.normalized
    except EmailNotValidError:
        return False, address
```

#### 3. `backend/app/core/dns_resolver.py`

```python
from __future__ import annotations
import asyncio
import dns.asyncresolver
import dns.rdatatype
import dns.exception
from app.core.models import DomainResult

async def resolve_domain(domain: str, timeout: float = 3.0) -> DomainResult:
    """
    Check MX records for domain. If no MX, fall back to A/AAAA.
    - Null MX (priority 0, exchange ".") → is_null_mx=True
    - NXDOMAIN, timeout, SERVFAIL, etc. → dns_error set, has_mx=False
    """
    resolver = dns.asyncresolver.Resolver()
    resolver.lifetime = timeout

    # --- MX lookup ---
    try:
        answer = await resolver.resolve(domain, dns.rdatatype.MX)
        for rdata in answer:
            if rdata.preference == 0 and str(rdata.exchange) == ".":
                return DomainResult(is_null_mx=True)
        return DomainResult(has_mx=True)
    except dns.resolver.NXDOMAIN:
        return DomainResult(dns_error="nxdomain")
    except dns.exception.Timeout:
        return DomainResult(dns_error="timeout")
    except dns.resolver.NoAnswer:
        pass  # no MX records; try A/AAAA below
    except Exception as exc:  # noqa: BLE001
        return DomainResult(dns_error=str(exc)[:80])

    # --- A/AAAA fallback ---
    for rdtype in (dns.rdatatype.A, dns.rdatatype.AAAA):
        try:
            await resolver.resolve(domain, rdtype)
            return DomainResult(has_a_aaaa=True)
        except dns.resolver.NXDOMAIN:
            return DomainResult(dns_error="nxdomain")
        except dns.exception.Timeout:
            return DomainResult(dns_error="timeout")
        except (dns.resolver.NoAnswer, Exception):  # noqa: BLE001
            continue

    return DomainResult(dns_error="no_records")
```

#### 4. `backend/app/core/lists.py`

Build a minimal disposable-domain list and a role-based prefix list.
The disposable list must be **vendored** (bundled in the repo as a plain text file), not fetched at runtime. We use a curated subset; you will add more in C5.

```python
"""
Loads disposable domains and role-based local-part prefixes from bundled text files.
Both files live in backend/app/core/data/.
"""
from __future__ import annotations
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def _load_set(filename: str) -> frozenset[str]:
    path = os.path.join(_DATA_DIR, filename)
    with open(path, encoding="utf-8") as fh:
        return frozenset(
            line.strip().lower() for line in fh if line.strip() and not line.startswith("#")
        )

_DISPOSABLE: frozenset[str] = _load_set("disposable_domains.txt")
_ROLE_PREFIXES: frozenset[str] = _load_set("role_prefixes.txt")

def is_disposable(domain: str) -> bool:
    return domain.lower() in _DISPOSABLE

def is_role_based(local_part: str) -> bool:
    return local_part.lower() in _ROLE_PREFIXES
```

Create `backend/app/core/data/disposable_domains.txt` with these domains (one per line):

```
# Disposable email domains — extend as needed
mailinator.com
guerrillamail.com
guerrillamail.net
guerrillamail.org
guerrillamail.biz
guerrillamail.de
yopmail.com
yopmail.fr
trashmail.com
trashmail.me
trashmail.net
throwam.com
throwaway.email
maildrop.cc
sharklasers.com
guerrillamailblock.com
grr.la
guerrillamail.info
spam4.me
fakeinbox.com
tempr.email
dispostable.com
spamgourmet.com
spamgourmet.net
spamgourmet.org
spamherelots.com
spamhere.eu
binkmail.com
bobmail.info
chammy.info
devnullmail.com
letthemeatspam.com
mailnull.com
spamthisplease.com
veryrealemail.com
```

Create `backend/app/core/data/role_prefixes.txt` with these (one per line):

```
# Role-based email local parts
abuse
admin
administrator
all
billing
contact
customer-service
customerservice
do-not-reply
donotreply
enquiries
ftp
help
helpdesk
hostmaster
info
it
list
mail
maildaemon
marketing
no-reply
noreply
office
postmaster
privacy
root
sales
security
service
siteowner
spam
support
sysadmin
tech
test
undisclosed-recipients
unsubscribe
usenet
uucp
webmaster
www
```

#### 5. `backend/app/core/assessor.py`

```python
"""
Top-level function: assess one email address.
Callers import only this module from core.
"""
from __future__ import annotations
from app.core.models import EmailResult, EmailStatus, DomainResult
from app.core.syntax import check_syntax
from app.core.dns_resolver import resolve_domain
from app.core.lists import is_disposable, is_role_based
from app.config import settings

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
        return EmailResult(address=normalised, status=EmailStatus.INVALID, domain=domain, checks=checks)
    elif dr.dns_error:
        checks["mx"] = "error"
        return EmailResult(address=normalised, status=EmailStatus.UNKNOWN, domain=domain, checks=checks)
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
```

---

### Tests to create

#### `backend/tests/test_syntax.py`

```python
import pytest
from app.core.syntax import check_syntax

@pytest.mark.parametrize("address,expected_ok", [
    ("user@example.com", True),
    ("User.Name+tag@sub.example.org", True),
    ("notanemail", False),
    ("@nodomain.com", False),
    ("no-at-sign", False),
    ("double@@domain.com", False),
])
def test_syntax(address: str, expected_ok: bool) -> None:
    ok, _ = check_syntax(address)
    assert ok is expected_ok
```

#### `backend/tests/test_lists.py`

```python
from app.core.lists import is_disposable, is_role_based

def test_disposable_domain() -> None:
    assert is_disposable("mailinator.com") is True

def test_legit_domain_not_disposable() -> None:
    assert is_disposable("gmail.com") is False

def test_role_prefix() -> None:
    assert is_role_based("admin") is True
    assert is_role_based("noreply") is True

def test_normal_prefix_not_role() -> None:
    assert is_role_based("vedant") is False
```

#### `backend/tests/test_assessor.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.core.assessor import assess
from app.core.models import EmailStatus, DomainResult

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
```

---

### How to run tests

```powershell
cd P:\mail_validator\backend
pytest tests/ -v
```

**Expected output:**

```
tests/test_health.py::test_health_returns_ok          PASSED
tests/test_syntax.py::test_syntax[user@example.com-True]  PASSED
tests/test_syntax.py::test_syntax[notanemail-False]       PASSED
... (6 parametrize cases)
tests/test_lists.py::test_disposable_domain           PASSED
tests/test_lists.py::test_legit_domain_not_disposable PASSED
tests/test_lists.py::test_role_prefix                 PASSED
tests/test_lists.py::test_normal_prefix_not_role      PASSED
tests/test_assessor.py::test_invalid_syntax           PASSED
tests/test_assessor.py::test_valid_email              PASSED
tests/test_assessor.py::test_disposable_email         PASSED
tests/test_assessor.py::test_role_email               PASSED
tests/test_assessor.py::test_dns_timeout_gives_unknown PASSED
tests/test_assessor.py::test_null_mx_gives_invalid    PASSED
14+ passed, 0 failed
```

---

### Exit gate for C1

- [ ] All 14+ tests pass, 0 failed
- [ ] `ruff check app tests` → clean
- [ ] `mypy app` → no errors
- [ ] `app/core/` has zero imports from `app.api` or `app.services`
- [ ] Git commit: `git commit -m "C1: validation core – syntax, DNS, scoring, lists"`
