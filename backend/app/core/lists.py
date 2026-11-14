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
