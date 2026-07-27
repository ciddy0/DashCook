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


def _row(**overrides):
    """A tickets row as asyncpg hands it back (metadata is raw JSON text)."""
    now = datetime.now(timezone.utc)
    return {
        "id": uuid4(),
        "category": "parser",
        "status": "open",
        "subject": "s",
        "description": "d",
        "recipe_url": None,
        "metadata": "{}",
        "submitter_ip_hash": None,
        "user_agent": None,
        "created_at": now,
        "updated_at": now,
        **overrides,
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
        return [_row()], 1

    monkeypatch.setattr(tickets_route, "list_tickets", fake_list_tickets)
    resp = client.get("/tickets", headers={"X-Admin-Token": "s3cret"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["category"] == "parser"


# ---- GET /tickets/{id} (admin) --------------------------------------------


def test_get_one_ticket_requires_token(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "s3cret")
    resp = client.get(f"/tickets/{uuid4()}", headers={"X-Admin-Token": "wrong"})
    assert resp.status_code == 401


def test_get_one_ticket_returns_200(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "s3cret")
    row = _row()

    async def fake_get_ticket(pool, ticket_id):
        return row

    monkeypatch.setattr(tickets_route, "get_ticket", fake_get_ticket)
    resp = client.get(f"/tickets/{row['id']}", headers={"X-Admin-Token": "s3cret"})
    assert resp.status_code == 200
    assert resp.json()["id"] == str(row["id"])


def test_get_one_missing_ticket_returns_404(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "s3cret")

    async def fake_get_ticket(pool, ticket_id):
        return None

    monkeypatch.setattr(tickets_route, "get_ticket", fake_get_ticket)
    resp = client.get(f"/tickets/{uuid4()}", headers={"X-Admin-Token": "s3cret"})
    assert resp.status_code == 404


# ---- PATCH /tickets/{id} (admin) ------------------------------------------


@pytest.fixture
def patchable(client, monkeypatch):
    """Client with a configured admin token and an in-memory update_ticket.

    The stub echoes the patch back the way the SQL does — an omitted field keeps
    its stored value — and records the kwargs it was called with.
    """
    monkeypatch.setattr(settings, "admin_token", "s3cret")
    stored = _row()
    calls: list[dict] = []

    async def fake_update_ticket(pool, ticket_id, *, status=None, category=None):
        calls.append({"id": ticket_id, "status": status, "category": category})
        if ticket_id != stored["id"]:
            return None
        if status is not None:
            stored["status"] = status
        if category is not None:
            stored["category"] = category
        stored["updated_at"] = datetime.now(timezone.utc)
        return stored

    monkeypatch.setattr(tickets_route, "update_ticket", fake_update_ticket)
    return client, stored, calls


def test_patch_without_config_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "")
    resp = client.patch(f"/tickets/{uuid4()}", json={"status": "closed"})
    assert resp.status_code == 503


def test_patch_wrong_token_returns_401(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "s3cret")
    resp = client.patch(
        f"/tickets/{uuid4()}",
        json={"status": "closed"},
        headers={"X-Admin-Token": "wrong"},
    )
    assert resp.status_code == 401


def test_patch_status_returns_updated_ticket(patchable):
    client, stored, calls = patchable
    resp = client.patch(
        f"/tickets/{stored['id']}",
        json={"status": "in_progress"},
        headers={"X-Admin-Token": "s3cret"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    # Category was not in the patch, so it must reach the db layer as None.
    assert calls[-1]["category"] is None


def test_patch_category_only_leaves_status(patchable):
    client, stored, _ = patchable
    resp = client.patch(
        f"/tickets/{stored['id']}",
        json={"category": "bug"},
        headers={"X-Admin-Token": "s3cret"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "bug"
    assert data["status"] == "open"


def test_patch_missing_ticket_returns_404(patchable):
    client, _, _ = patchable
    resp = client.patch(
        f"/tickets/{uuid4()}",
        json={"status": "closed"},
        headers={"X-Admin-Token": "s3cret"},
    )
    assert resp.status_code == 404


def test_patch_empty_body_is_rejected(patchable):
    client, stored, _ = patchable
    resp = client.patch(
        f"/tickets/{stored['id']}", json={}, headers={"X-Admin-Token": "s3cret"}
    )
    assert resp.status_code == 422


def test_patch_invalid_status_is_rejected(patchable):
    client, stored, _ = patchable
    resp = client.patch(
        f"/tickets/{stored['id']}",
        json={"status": "nonsense"},
        headers={"X-Admin-Token": "s3cret"},
    )
    assert resp.status_code == 422


def test_patch_immutable_field_is_rejected(patchable):
    """Submitted content is not admin-editable — extra keys must 422."""
    client, stored, _ = patchable
    resp = client.patch(
        f"/tickets/{stored['id']}",
        json={"status": "closed", "subject": "rewritten"},
        headers={"X-Admin-Token": "s3cret"},
    )
    assert resp.status_code == 422


def test_patch_malformed_uuid_is_rejected(patchable):
    client, _, _ = patchable
    resp = client.patch(
        "/tickets/not-a-uuid",
        json={"status": "closed"},
        headers={"X-Admin-Token": "s3cret"},
    )
    assert resp.status_code == 422
