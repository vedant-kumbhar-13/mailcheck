from app.services.rate_limiter import RateLimiter


def test_ip_key_is_hashed_not_raw() -> None:
    rl = RateLimiter(limit=10, window_seconds=60)
    raw = "192.168.1.100"
    rl.hit(raw)
    # The key stored must NOT equal the raw IP
    assert raw not in rl._buckets
    # It should be a hex string
    for key in rl._buckets:
        assert all(c in "0123456789abcdef" for c in key), f"Key '{key}' is not a hex hash"


def test_different_ips_have_different_keys() -> None:
    rl = RateLimiter(limit=10, window_seconds=60)
    rl.hit("1.1.1.1")
    rl.hit("2.2.2.2")
    assert len(rl._buckets) == 2


def test_same_ip_accumulates() -> None:
    rl = RateLimiter(limit=10, window_seconds=60)
    for _ in range(3):
        rl.hit("1.1.1.1")
    assert sum(len(v) for v in rl._buckets.values()) == 3
