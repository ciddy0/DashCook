"""Coverage for the support-ticket endpoints.

Mirrors tests/test_rate_limit.py: the app is exercised through TestClient
without the lifespan context (so no real Postgres pool is needed); the db layer
is stubbed and the pool dependency is overridden with a dummy object.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import routes.tickets as tickets_route
from config import get_settings
from dependencies import get_pool
from main import app
from middleware.rate_limiter import limiter

settings = get_settings()

VALID_BODY = {
    "category": "parser",
    "subject": "Parser failed",
    "description": "The recipe at example.com did not parse.",
}


def _limit_count(limit_str: str) -> int:
    """'2/minute;5/hour' -> 2 (the first / most restrictive window)."""
    return int(limit_str.split(";")[0].split("/")[0])


@pytest.fixture
def client(monkeypatch):
    limiter.reset()
    app.dependency_overrides[get_pool] = lambda: object()

    async def fake_create_ticket(pool, **kwargs):
        return {
            "id": kwargs["id"],
            "status": "open",
            "created_at": datetime.now(timezone.utc),
        }

    monkeypatch.setattr(tickets_route, "create_ticket", fake_create_ticket)
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()
    limiter.reset()


# ---- POST /tickets --------------------------------------------------------


def test_create_ticket_returns_201(client):
    resp = client.post("/tickets", json=VALID_BODY)
    assert resp.status_code == 201
    data = resp.json()
    assert set(data) == {"id", "status", "created_at"}
    assert data["status"] == "open"


def test_unknown_field_is_rejected(client):
    body = {**VALID_BODY, "surprise": "boo"}
    assert client.post("/tickets", json=body).status_code == 422


def test_overlong_field_is_rejected(client):
    body = {**VALID_BODY, "description": "x" * 5001}
    assert client.post("/tickets", json=body).status_code == 422


def test_invalid_category_is_rejected(client):
    body = {**VALID_BODY, "category": "nonsense"}
    assert client.post("/tickets", json=body).status_code == 422


def test_malformed_json_is_rejected(client):
    resp = client.post(
        "/tickets", content="{", headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 422


def test_oversized_body_returns_413(client):
    body = {**VALID_BODY, "description": "x" * 4000, "metadata": {}}
    # Pad with a big header-declared body via raw content beyond the 16 KB cap.
    huge = "y" * (settings.max_request_body_bytes + 1)
    resp = client.post(
        "/tickets", content=huge, headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 413


def test_post_rate_limit_returns_429(client):
    limit = _limit_count(settings.rate_limit_ticket)
    statuses = [
        client.post("/tickets", json=VALID_BODY).status_code
        for _ in range(limit + 1)
    ]
    assert statuses[:limit] == [201] * limit
    assert statuses[-1] == 429


# ---- GET /tickets (admin) -------------------------------------------------


def test_get_tickets_without_config_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "")
    assert client.get("/tickets").status_code == 503


def test_get_tickets_wrong_token_returns_401(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "s3cret")
    resp = client.get("/tickets", headers={"X-Admin-Token": "wrong"})
    assert resp.status_code == 401


def test_get_tickets_valid_token_returns_200(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "s3cret")

    async def fake_list_tickets(pool, **kwargs):
        row = {
            "id": uuid4(),
            "category": "parser",
            "status": "open",
            "subject": "s",
            "description": "d",
            "recipe_url": None,
            "metadata": "{}",
            "submitter_ip_hash": None,
            "user_agent": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        return [row], 1

    monkeypatch.setattr(tickets_route, "list_tickets", fake_list_tickets)
    resp = client.get("/tickets", headers={"X-Admin-Token": "s3cret"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["category"] == "parser"
