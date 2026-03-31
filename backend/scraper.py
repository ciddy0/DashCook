import httpx

async def fetch_page(url: str) -> str:
    """
    basically just fetch the html from a given url
    TO-DO: add some sanitation (malicous urls)
    """
    HEADERS = {"User-agent": "DashCook/0.1"}

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        max_redirects=3,
    ) as client:
        response = await client.get(url, headers = HEADERS)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            raise ValueError(f"expected html but got: {content_type} D:")
        
        return response.text

