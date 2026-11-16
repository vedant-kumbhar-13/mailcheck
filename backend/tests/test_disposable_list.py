from app.core.lists import is_disposable


def test_extended_list_loaded() -> None:
    assert is_disposable("10minutemail.com") is True
    assert is_disposable("yopmail.com") is True
    assert is_disposable("fakeinbox.com") is True


def test_legit_still_not_disposable() -> None:
    assert is_disposable("gmail.com") is False
    assert is_disposable("outlook.com") is False
