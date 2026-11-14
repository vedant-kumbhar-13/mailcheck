from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Read the rightmost IP from X-Forwarded-For (last hop only).
    Falls back to request.client.host.
    """
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"
