import httpx

MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB


async def fetch_page(url: str) -> str:
    """
    basically just fetch the html from a given url
    """
    HEADERS = {"User-agent": "DashCook/0.1"}

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        max_redirects=3,
    ) as client:
        async with client.stream("GET", url, headers=HEADERS) as response:
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

    return b"".join(chunks).decode("utf-8", errors="replace")
