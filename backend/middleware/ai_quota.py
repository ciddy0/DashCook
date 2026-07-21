"""Shared daily budget for the Claude-backed endpoints.

/ask and /discover draw from one pool (settings.rate_limit_ai) so a visitor has
a single, explainable allowance per day rather than one per feature. Counters
live in slowapi's in-process storage — the same place the @limiter.limit
decorators keep theirs — so there is no new infrastructure, at the cost of the
budget resetting on deploy and being per-replica.

Callers check has_budget() first and only consume() once the Claude call has
actually succeeded, so an API outage never burns someone's allowance.
"""

from functools import lru_cache

from limits import RateLimitItem, parse

from config import get_settings
from middleware.rate_limiter import get_client_ip, limiter

_NAMESPACE = "ai"


@lru_cache
def _daily() -> RateLimitItem:
    return parse(get_settings().rate_limit_ai)


def has_budget(request) -> bool:
    """Whether the caller has at least one AI request left today. Consumes nothing."""
    return limiter.limiter.test(_daily(), _NAMESPACE, get_client_ip(request))


def consume(request) -> bool:
    """Spend one request from today's budget. False if it was already empty."""
    return limiter.limiter.hit(_daily(), _NAMESPACE, get_client_ip(request))


def remaining(request) -> int:
    """How many AI requests the caller has left today."""
    return limiter.limiter.get_window_stats(
        _daily(), _NAMESPACE, get_client_ip(request)
    ).remaining
