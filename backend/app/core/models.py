from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EmailStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    RISKY = "risky"
    UNKNOWN = "unknown"


@dataclass
class DomainResult:
    """Raw DNS findings for a domain."""

    has_mx: bool = False
    has_a_aaaa: bool = False
    is_null_mx: bool = False  # RFC 7505: "0 ." record
    dns_error: str | None = None  # set when lookup failed


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
