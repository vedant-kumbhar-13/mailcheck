from __future__ import annotations

import hashlib
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


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


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key_hash: str = ""  # SHA-256 of the raw job key
    status: JobStatus = JobStatus.PENDING
    total: int = 0
    done: int = 0
    error: str | None = None
    results: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None

    @staticmethod
    def new(total: int) -> tuple[Job, str]:
        """Create a new job and return (job, raw_key)."""
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        job = Job(total=total, key_hash=key_hash)
        return job, raw_key
