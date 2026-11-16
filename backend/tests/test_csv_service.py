from io import BytesIO

import pytest
from fastapi import UploadFile

from app.services.csv_service import CsvError, parse_csv


def make_upload(content: bytes, filename: str = "test.csv") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))


@pytest.mark.asyncio
async def test_valid_csv_with_header() -> None:
    data = b"email\nuser@example.com\nadmin@test.org\n"
    result = await parse_csv(make_upload(data))
    assert "user@example.com" in result
    assert "admin@test.org" in result


@pytest.mark.asyncio
async def test_csv_too_large() -> None:
    big = b"email\n" + b"a@b.com\n" * 400_000
    with pytest.raises(CsvError) as exc:
        await parse_csv(make_upload(big))
    assert exc.value.code == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_csv_binary_rejection() -> None:
    data = b"email\nuser@example.com\x00binary"
    with pytest.raises(CsvError) as exc:
        await parse_csv(make_upload(data))
    assert exc.value.code == "CSV_PARSE_ERROR"


@pytest.mark.asyncio
async def test_csv_no_email_column() -> None:
    data = b"name,phone\nAlice,555-1234\n"
    with pytest.raises(CsvError) as exc:
        await parse_csv(make_upload(data))
    assert exc.value.code == "INVALID_EMAIL_COLUMN"
