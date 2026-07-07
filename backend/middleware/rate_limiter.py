from slowapi import Limiter


def get_client_ip(request) -> str:
    """slowapi key function: proxy-aware client IP.

    Uses the first X-Forwarded-For entry when present (we run behind the
    Azure Container Apps ingress), falling back to the socket peer.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

limiter = Limiter(
    key_func=get_client_ip,
    headers_enabled=True,
    retry_after="delta-seconds",
)
