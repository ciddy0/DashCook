from collections import defaultdict
from time import time

from config import get_settings

settings = get_settings()
RATE_LIMIT = settings.rate_limit
WINDOW_SECONDS = 3600

_request_log: dict[str, list[float]] = defaultdict(list)


def get_client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def check_rate_limit(ip: str) -> tuple[bool, int]:
    """
    returns (allowed, retry_after_seconds). retry_after is 0 if allowed.
    """
    now = time()
    cutoff = now - WINDOW_SECONDS

    _request_log[ip] = [t for t in _request_log[ip] if t > cutoff]

    if len(_request_log[ip]) >= RATE_LIMIT:
        oldest = _request_log[ip][0]
        retry_after = int(oldest + WINDOW_SECONDS - now) + 1
        return False, retry_after

    _request_log[ip].append(now)
    return True, 0
