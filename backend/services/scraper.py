import asyncio
import random
import time
from urllib.parse import urlparse

import httpx

MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_RETRIES = 2
MIN_DOMAIN_DELAY = 2.0  # seconds between requests to the same domain

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
]

# tracks last request timestamp per domain for rate limiting
_domain_last_request: dict[str, float] = {}


def _build_headers(user_agent: str | None = None) -> dict[str, str]:
    return {
        "User-Agent": user_agent or random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


async def _enforce_domain_delay(url: str) -> None:
    domain = urlparse(url).netloc
    now = time.monotonic()
    last = _domain_last_request.get(domain)
    if last is not None:
        elapsed = now - last
        if elapsed < MIN_DOMAIN_DELAY:
            await asyncio.sleep(MIN_DOMAIN_DELAY - elapsed)
    _domain_last_request[domain] = time.monotonic()


async def _fetch_with_httpx(url: str, headers: dict[str, str]) -> bytes:
    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        max_redirects=3,
    ) as client:
        async with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                raise ValueError(f"expected html but got: {content_type} D:")

            chunks = []
            total_bytes = 0

            async for chunk in response.aiter_bytes():
                total_bytes += len(chunk)
                if total_bytes > MAX_RESPONSE_BYTES:
                    raise ValueError(
                        f"Response exceeds maximum allowed size of "
                        f"{MAX_RESPONSE_BYTES // (1024 * 1024)} MB"
                    )
                chunks.append(chunk)

    return b"".join(chunks)


def _fetch_with_cloudscraper(url: str, headers: dict[str, str]) -> bytes:
    import cloudscraper

    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise ValueError(f"expected html but got: {content_type} D:")

    if len(resp.content) > MAX_RESPONSE_BYTES:
        raise ValueError(
            f"Response exceeds maximum allowed size of "
            f"{MAX_RESPONSE_BYTES // (1024 * 1024)} MB"
        )

    return resp.content


async def fetch_page(url: str) -> str:
    """
    basically just fetch the html from a given url
    """
    await _enforce_domain_delay(url)

    last_exc = None
    for attempt in range(1 + MAX_RETRIES):
        headers = _build_headers()

        if attempt > 0:
            jitter = random.uniform(1, 3)
            await asyncio.sleep(jitter)

        try:
            raw = await _fetch_with_httpx(url, headers)
            return raw.decode("utf-8", errors="replace")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (403, 429):
                last_exc = exc
                continue
            raise

    # all httpx retries exhausted on 403/429 — try cloudscraper as fallback
    try:
        raw = await asyncio.to_thread(
            _fetch_with_cloudscraper, url, _build_headers()
        )
        return raw.decode("utf-8", errors="replace")
    except Exception:
        # if cloudscraper also fails, raise the original httpx error
        raise last_exc
