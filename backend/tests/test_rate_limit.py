"""Rate-limiting coverage for the public API.

These hit the real app so the actual @limiter.limit decorators and the 429
exception handler are exercised. TestClient is used WITHOUT the context-manager
form on purpose: that skips the lifespan startup (which would connect to
Postgres). DB/network calls are stubbed, so no real pool is needed.
"""

import pytest
from fastapi.testclient import TestClient

import routes.recipes as recipes_route
from config import get_settings
from dependencies import get_pool
from main import app
from middleware.rate_limiter import limiter

settings = get_settings()


def _limit_count(limit_str: str) -> int:
    """'60/minute' -> 60."""
    return int(limit_str.split("/")[0])


@pytest.fixture
def client():
    # Fresh limiter counters for every test so counts don't leak across tests.
    limiter.reset()
    # Dummy pool: our stubbed db calls ignore it, but the dependency must resolve.
    app.dependency_overrides[get_pool] = lambda: object()
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()
    limiter.reset()


def test_read_endpoint_returns_429_after_limit(client, monkeypatch):
    async def fake_list_categories(pool):
        return []

    monkeypatch.setattr(recipes_route, "list_categories", fake_list_categories)

    limit = _limit_count(settings.rate_limit_read)
    statuses = [client.get("/categories").status_code for _ in range(limit + 1)]

    assert statuses[:limit] == [200] * limit, "requests within the limit should pass"
    assert statuses[-1] == 429, "the request over the limit should be throttled"

    resp = client.get("/categories")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


def test_expensive_endpoint_returns_429_after_limit(client, monkeypatch):
    async def fake_extract_recipe(pool, url):
        return {
            "title": "t",
            "ingredients": [],
            "instructions": [],
            "source_url": url,
        }

    monkeypatch.setattr(recipes_route, "extract_recipe", fake_extract_recipe)

    limit = _limit_count(settings.rate_limit_expensive)
    body = {"url": "https://example.com/recipe"}
    statuses = [
        client.post("/url", json=body).status_code for _ in range(limit + 1)
    ]

    assert statuses[-1] == 429
    assert client.post("/url", json=body).headers.get("Retry-After") is not None


def test_health_endpoints_are_exempt(client):
    # Well past any configured limit; health checks must never be throttled.
    statuses = [client.get("/ping").status_code for _ in range(100)]
    assert set(statuses) == {200}
