import pytest

from app.core.syntax import check_syntax


@pytest.mark.parametrize(
    "address,expected_ok",
    [
        ("user@example.com", True),
        ("User.Name+tag@sub.example.org", True),
        ("notanemail", False),
        ("@nodomain.com", False),
        ("no-at-sign", False),
        ("double@@domain.com", False),
    ],
)
def test_syntax(address: str, expected_ok: bool) -> None:
    ok, _ = check_syntax(address)
    assert ok is expected_ok
