"""Coverage for RAG discovery (POST /discover) and the shared AI budget.

Mirrors tests/test_rate_limit.py: the app is exercised through TestClient
without the lifespan context (so no real Postgres pool is needed); the db,
embedding and Claude calls are stubbed and the pool dependency is overridden
with a dummy object.
"""

import pytest
from fastapi.testclient import TestClient

import routes.recipes as recipes_route
from config import get_settings
from dependencies import get_pool
from main import app
from middleware.rate_limiter import limiter
from services.recipe_discovery import _validate_picks

settings = get_settings()

DAILY_BUDGET = int(settings.rate_limit_ai.split("/")[0])

CANDIDATES = [
    {
        "title": "Beef Bourguignon",
        "source_url": "https://example.com/beef",
        "image_url": None,
        "total_time": "3 hours",
        "servings": "6",
        "category": "Mains",
        "ingredients": ["beef chuck", "red wine"],
        "distance": 0.1,
    },
    {
        "title": "Chicken Pot Pie",
        "source_url": "https://example.com/pie",
        "image_url": None,
        "total_time": "1 hour",
        "servings": "4",
        "category": "Mains",
        "ingredients": ["chicken", "butter"],
        "distance": 0.2,
    },
]

QUESTION_BODY = {
    "question": "Can I use oil instead of butter?",
    "title": "Chicken Pot Pie",
    "ingredients": ["2 tbsp butter"],
}


@pytest.fixture
def client(monkeypatch):
    # Fresh counters per test so the daily budget doesn't leak across tests.
    limiter.reset()
    app.dependency_overrides[get_pool] = lambda: object()

    monkeypatch.setattr(recipes_route.settings, "anthropic_api_key", "test-key")

    async def fake_embed_query(text):
        return [0.0] * 8

    async def fake_search_detailed(pool, embedding, limit):
        return CANDIDATES

    monkeypatch.setattr(recipes_route, "embed_query", fake_embed_query)
    monkeypatch.setattr(recipes_route, "search_recipes_detailed", fake_search_detailed)

    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()
    limiter.reset()


def _stub_picks(monkeypatch, intro="Cosy picks:", indexes=(0,)):
    async def fake_pick_recipes(query, candidates, limit):
        return intro, [{**candidates[i], "why": "slow-braised"} for i in indexes]

    monkeypatch.setattr(recipes_route, "pick_recipes", fake_pick_recipes)


# ---- POST /discover -------------------------------------------------------


def test_discover_returns_ai_picks(client, monkeypatch):
    _stub_picks(monkeypatch)

    resp = client.post("/discover", json={"query": "cozy warm dinners"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "ai"
    assert data["answer"] == "Cosy picks:"
    assert [r["title"] for r in data["recipes"]] == ["Beef Bourguignon"]
    assert data["recipes"][0]["why"] == "slow-braised"
    assert data["remaining"] == DAILY_BUDGET - 1


def test_discover_respects_limit(client, monkeypatch):
    _stub_picks(monkeypatch, indexes=(0, 1))

    resp = client.post("/discover", json={"query": "dinner", "limit": 2})

    assert len(resp.json()["recipes"]) == 2


def test_discover_falls_back_to_search_when_budget_is_spent(client, monkeypatch):
    _stub_picks(monkeypatch)

    for _ in range(DAILY_BUDGET):
        assert client.post("/discover", json={"query": "cozy"}).json()["mode"] == "ai"

    data = client.post("/discover", json={"query": "cozy"}).json()

    # Out of AI budget is not an error: same shape, plain search results.
    assert data["mode"] == "search"
    assert data["answer"] is None
    assert [r["title"] for r in data["recipes"]] == [c["title"] for c in CANDIDATES]
    assert all(r["why"] is None for r in data["recipes"])
    assert data["remaining"] == 0


def test_discover_falls_back_when_assistant_errors_without_spending_budget(
    client, monkeypatch
):
    async def boom(query, candidates, limit):
        raise RuntimeError("anthropic down")

    monkeypatch.setattr(recipes_route, "pick_recipes", boom)

    data = client.post("/discover", json={"query": "cozy"}).json()

    assert data["mode"] == "search"
    assert data["recipes"], "fallback should still return the vector-search hits"
    # A failed call must not cost the user one of their daily requests.
    assert data["remaining"] == DAILY_BUDGET


def test_discover_falls_back_when_nothing_fits(client, monkeypatch):
    _stub_picks(monkeypatch, intro="Nothing here fits.", indexes=())

    data = client.post("/discover", json={"query": "sushi"}).json()

    assert data["mode"] == "search"
    assert data["remaining"] == DAILY_BUDGET


def test_discover_rejects_empty_query(client):
    assert client.post("/discover", json={"query": "   "}).status_code == 422


# ---- Shared budget across /ask and /discover ------------------------------


def test_ask_and_discover_share_one_daily_budget(client, monkeypatch):
    _stub_picks(monkeypatch)

    async def fake_answer_question(**kwargs):
        return "Yes, olive oil works."

    monkeypatch.setattr(recipes_route, "answer_question", fake_answer_question)

    for _ in range(DAILY_BUDGET):
        assert client.post("/ask", json=QUESTION_BODY).status_code == 200

    # /ask exhausted the shared pool, so /discover has nothing left to spend.
    assert client.post("/ask", json=QUESTION_BODY).status_code == 429
    assert client.post("/discover", json={"query": "cozy"}).json()["mode"] == "search"


def test_failed_ask_does_not_spend_budget(client, monkeypatch):
    async def boom(**kwargs):
        raise RuntimeError("anthropic down")

    monkeypatch.setattr(recipes_route, "answer_question", boom)
    _stub_picks(monkeypatch)

    assert client.post("/ask", json=QUESTION_BODY).status_code == 503
    assert client.post("/discover", json={"query": "cozy"}).json()["remaining"] == (
        DAILY_BUDGET - 1
    )


# ---- Pick validation ------------------------------------------------------


def test_validate_picks_drops_ids_that_are_not_on_the_shortlist():
    picks = _validate_picks(
        [
            {"id": 99, "why": "invented"},
            {"id": 0, "why": "out of range"},
            {"id": 2, "why": "real"},
            {"id": 2, "why": "duplicate"},
            "not a dict",
        ],
        CANDIDATES,
        limit=5,
    )

    assert [p["title"] for p in picks] == ["Chicken Pot Pie"]
    assert picks[0]["why"] == "real"


def test_validate_picks_caps_at_limit():
    picks = _validate_picks(
        [{"id": 1, "why": "a"}, {"id": 2, "why": "b"}], CANDIDATES, limit=1
    )

    assert len(picks) == 1
