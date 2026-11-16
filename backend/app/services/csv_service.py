"""
CSV parsing with hardened constraints.
- Streaming read up to MAX_CSV_BYTES.
- Max MAX_CSV_ROWS data rows.
- UTF-8 with optional BOM.
- Binary content rejection.
- Strict csv.reader parsing.
- Returns list of raw email strings (not yet validated).
"""

from __future__ import annotations

import csv
import io

from fastapi import UploadFile

from app.config import settings


class CsvError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


async def parse_csv(file: UploadFile) -> list[str]:
    """
    Parse uploaded CSV. Returns a list of raw email strings.
    Raises CsvError on any structural problem.
    """
    # 1. Read up to MAX_CSV_BYTES + 1 (to detect over-limit)
    raw = await file.read(settings.max_csv_bytes + 1)
    if len(raw) > settings.max_csv_bytes:
        raise CsvError("FILE_TOO_LARGE", f"File exceeds {settings.max_csv_bytes} bytes")

    # 2. Reject binary content (null bytes)
    if b"\x00" in raw:
        raise CsvError("CSV_PARSE_ERROR", "Binary content detected")

    # 3. Decode UTF-8 with BOM
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise CsvError("CSV_PARSE_ERROR", f"Encoding error: {e}") from e

    # 4. Parse CSV
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise CsvError("CSV_PARSE_ERROR", "Empty file")

    # 5. Find email column
    headers = [h.strip().lower() for h in rows[0]]
    email_col: int | None = None
    for candidate in ("email", "email address", "e-mail", "emailaddress"):
        if candidate in headers:
            email_col = headers.index(candidate)
            break

    data_rows: list[list[str]]
    if email_col is None:
        # Try first column as fallback if no header looks like email
        # but only if the first row looks like a header (non-email value)
        from app.core.syntax import check_syntax

        first_cell = rows[0][0].strip() if rows[0] else ""
        ok, _ = check_syntax(first_cell)
        if ok:
            # First row is actual data, no header; treat col 0 as emails
            email_col = 0
            data_rows = rows
        else:
            raise CsvError(
                "INVALID_EMAIL_COLUMN",
                "Could not find an 'email' column. "
                "Please name your column: email, e-mail, or email address.",
            )
    else:
        data_rows = rows[1:]  # skip header row

    # 6. Extract emails, enforce row limit
    emails: list[str] = []
    for row in data_rows:
        if len(emails) >= settings.max_csv_rows:
            break
        if len(row) > email_col:
            val = row[email_col].strip()
            if val:
                emails.append(val)

    if not emails:
        raise CsvError("CSV_PARSE_ERROR", "No email addresses found in file")

    return emails
