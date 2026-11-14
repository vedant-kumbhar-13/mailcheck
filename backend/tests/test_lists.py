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
