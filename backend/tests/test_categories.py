"""Endpoint + DB-layer wiring tests for categories, using a stub asyncpg pool.

No live database: a FakePool returns canned rows so we can verify the /recipes and
/categories endpoints, the category filter, and card mapping.
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import main
from dependencies import get_pool

CATEGORIES = [
    {"id": 1, "name": "Desserts", "description": "Sweet treats"},
    {"id": 2, "name": "Pasta", "description": "Noodly things"},
]

RECIPES = [
    {"url": "https://ex.com/cake", "title": "Cake", "image_url": None,
     "prep_time": None, "cook_time": None, "total_time": None, "servings": None,
     "created_at": datetime(2026, 7, 3, tzinfo=timezone.utc), "category": "Desserts",
     "section_id": 1},
    {"url": "https://ex.com/pie", "title": "Pie", "image_url": None,
     "prep_time": None, "cook_time": None, "total_time": None, "servings": None,
     "created_at": datetime(2026, 7, 2, tzinfo=timezone.utc), "category": "Desserts",
     "section_id": 1},
    {"url": "https://ex.com/penne", "title": "Penne", "image_url": None,
     "prep_time": None, "cook_time": None, "total_time": None, "servings": None,
     "created_at": datetime(2026, 7, 1, tzinfo=timezone.utc), "category": "Pasta",
     "section_id": 2},
]
RECIPES.sort(key=lambda r: (r["created_at"], r["url"]), reverse=True)


class FakeConn:
    async def fetch(self, sql, *args):
        if "FROM categories" in sql and "recipes" not in sql:
            return CATEGORIES
        # list_recipes: args = (cursor_ts, cursor_url, category_id, limit+1)
        cursor_ts, cursor_url, category_id, lim = args
        rows = RECIPES
        if cursor_ts is not None:
            rows = [r for r in rows if (r["created_at"], r["url"]) < (cursor_ts, cursor_url)]
        if category_id is not None:
            rows = [r for r in rows if r["section_id"] == category_id]
        return rows[:lim]


class FakeAcquire:
    async def __aenter__(self):
        return FakeConn()

    async def __aexit__(self, *a):
        return False


class FakePool:
    def acquire(self):
        return FakeAcquire()


@pytest.fixture
def client():
    main.app.dependency_overrides[get_pool] = lambda: FakePool()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_get_categories(client):
    r = client.get("/categories")
    assert r.status_code == 200
    assert [c["name"] for c in r.json()] == ["Desserts", "Pasta"]


def test_recipes_include_category(client):
    r = client.get("/recipes")
    assert r.status_code == 200
    items = r.json()["items"]
    assert all("category" in i for i in items)
    assert items[0]["category"] in {"Desserts", "Pasta"}


def test_filter_by_category(client):
    r = client.get("/recipes?category=2")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Penne"
    assert items[0]["category"] == "Pasta"


def test_invalid_category_rejected(client):
    assert client.get("/recipes?category=0").status_code == 422
