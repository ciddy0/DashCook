# DashCook API — SousChat

> Extract clean, structured recipes from bloated, ad-heavy recipe websites.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Postgres](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Deploy](https://img.shields.io/badge/Deploy-Azure%20Container%20Apps-0078D4?logo=microsoftazure&logoColor=white)

DashCook is the FastAPI backend behind **SousChat**. Give it a URL to a recipe page and it
scrapes the page, strips away the life story and ads, and returns clean structured JSON —
parsed ingredients, ordered instructions, times, servings, and an image. Results are cached
in Postgres, embedded for semantic search, and automatically organized into an LLM-named
category taxonomy.

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Rate limiting](#rate-limiting)
- [Data model & migrations](#data-model--migrations)
- [Maintenance scripts](#maintenance-scripts)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Overview

Recipe websites are notoriously bloated — pages of narrative, ads, and pop-ups wrapped around
a few lines of actual cooking. DashCook takes a recipe URL and returns just the recipe:

- **Structured extraction** — title, image, prep/cook/total time, servings, ordered
  instructions, and ingredients parsed into `{ name, quantity, quantity_max, unit, scalable }`.
- **Caching** — every extracted recipe is stored in Postgres, so repeat requests are instant
  and don't re-scrape the source.
- **Semantic search & recommendations** — each recipe is embedded with OpenAI, enabling
  free-text search and "similar recipes" via pgvector distance.
- **Automatic categories** — recipes are clustered and each cluster is named by an LLM, then
  new recipes are auto-assigned to the nearest category at ingest time.

---

## Features

- 🧹 **Recipe extraction & normalization** from arbitrary recipe pages
- 🥕 **Ingredient parsing** into name / quantity / unit / scalable
- 💾 **DB-backed caching** of extracted recipes
- 🔎 **Semantic search** over recipes (`GET /search`)
- 🧭 **Similar-recipe recommendations** (`GET /similar`)
- 🏷️ **Auto category taxonomy** via clustering + LLM naming
- 📄 **Cursor-based pagination** for the recipe list
- 🚦 **Tiered per-IP rate limiting** to keep the public API from being abused

---

## Tech stack

| Concern            | Choice                                                        |
| ------------------ | ------------------------------------------------------------- |
| Web framework      | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn            |
| Database           | PostgreSQL 16 + [pgvector](https://github.com/pgvector/pgvector) |
| DB driver          | [asyncpg](https://github.com/MagicStack/asyncpg)              |
| Embeddings / LLM   | OpenAI (`text-embedding-3-large`, `gpt-4o-mini` for cluster naming) |
| Scraping           | `httpx`, `cloudscraper`, BeautifulSoup                        |
| Rate limiting      | [slowapi](https://github.com/laurentS/slowapi)                |
| Tests              | pytest                                                        |
| Container / deploy | Docker → Azure Container Apps (GitHub Actions)                |

---

## Architecture

The core extraction flow (`services/recipe_service.py`) for `POST /url`:

```
POST /url
   │
   ▼
normalize_url ──► validate_url ──► cache hit? ──yes──► return cached Recipe
                                      │ no
                                      ▼
                               fetch_page (scrape HTML)
                                      │
                                      ▼
                               parse_recipe (structured data)
                                      │
                                      ▼
                             generate_embedding (OpenAI)
                                      │
                                      ▼
                        assign_category (nearest centroid)
                                      │
                                      ▼
                          cache_recipe (store in Postgres)
                                      │
                                      ▼
                                return Recipe
```

Category assignment happens two ways:

- **At ingest (per request):** `db/categories.py::assign_category` puts each new recipe into
  the nearest existing category centroid.
- **Offline (occasional):** `scripts/build_categories.py` rebuilds the whole taxonomy by
  clustering all embeddings (UMAP → K-Means, best K by silhouette) and naming each cluster
  with an LLM. Run it when you want to refresh categories; new recipes are handled
  automatically in between.

---

## Project structure

```
backend/
├── main.py                 # FastAPI app: lifespan, CORS, rate-limit wiring, routers
├── config.py               # Pydantic settings (env-driven)
├── dependencies.py         # Shared FastAPI dependencies (DB pool injection)
├── routes/                 # HTTP endpoints
│   ├── recipes.py          #   /url, /recipes, /categories, /similar, /search
│   └── health.py           #   /, /ping
├── services/               # Business logic
│   ├── recipe_service.py   #   extraction orchestration
│   ├── scraper.py          #   page fetching (per-domain throttling)
│   ├── parser.py           #   HTML → structured recipe
│   ├── ingredient_parser.py#   ingredient string → name/quantity/unit
│   └── embedder.py         #   OpenAI embeddings
├── db/                     # Data access
│   ├── pool.py             #   asyncpg connection pool
│   ├── recipes.py          #   recipe queries (cache, list, search, similar)
│   ├── categories.py       #   category queries + assign_category
│   └── migrations/         #   ordered SQL migrations
├── models/                 # Pydantic request/response models
├── middleware/
│   └── rate_limiter.py     # slowapi Limiter (per-IP, X-Forwarded-For aware)
├── utils/                  # pagination cursors, URL helpers
├── scripts/                # seed, backfill_embeddings, build_categories
├── tests/                  # pytest suite
├── experiments/            # clustering experiments (not part of the running service)
├── Dockerfile
└── docker-compose.yml      # local Postgres + pgvector
```

---

## Getting started

### Prerequisites

- Python 3.11
- Docker (for local Postgres + pgvector)

### 1. Start the database

```bash
docker compose up -d
```

This runs `pgvector/pgvector:pg16` and exposes Postgres on **port 5433** with
`dashcook`/`dashcook` credentials (see `docker-compose.yml`).

### 2. Install dependencies

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in `backend/` (see [Environment variables](#environment-variables)):

```env
DATABASE_URL=postgresql://dashcook:dashcook@localhost:5433/dashcook
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
OPENAI_API_KEY=sk-...
RATE_LIMIT_EXPENSIVE=30/hour
RATE_LIMIT_READ=60/minute
```

### 4. Apply migrations

The SQL in `db/migrations/` is applied in numeric order. These migrations evolve an existing
`recipes` table and set up the `vector(3072)` embedding column:

```bash
for f in db/migrations/*.sql; do
  psql "postgresql://dashcook:dashcook@localhost:5433/dashcook" -f "$f"
done
```

### 5. Run the API

```bash
uvicorn main:app --reload
```

Interactive docs: <http://localhost:8000/docs> · OpenAPI: <http://localhost:8000/openapi.json>

---

## Environment variables

Configuration is loaded by `config.py` from `.env` (extra keys are ignored). All values have
defaults except the OpenAI key, which is required for embeddings, search, and categorization.

| Variable               | Default                                                     | Required | Description                                         |
| ---------------------- | ---------------------------------------------------------- | -------- | --------------------------------------------------- |
| `DATABASE_URL`         | `postgresql://dashcook:dashcook@localhost:5433/dashcook`   | No       | Local Postgres connection string                    |
| `SUPABASE_URL`         | `None`                                                     | No       | Production Postgres URL; used instead of `DATABASE_URL` when set |
| `CORS_ORIGINS`         | `http://localhost:5173,http://localhost:3000`              | No       | Comma-separated allowed origins                     |
| `OPENAI_API_KEY`       | `""`                                                       | **Yes**  | OpenAI key for embeddings + cluster naming          |
| `RATE_LIMIT_EXPENSIVE` | `30/hour`                                                  | No       | Limit for OpenAI-backed endpoints (`/url`, `/search`) |
| `RATE_LIMIT_READ`      | `60/minute`                                                | No       | Limit for cheap read endpoints                      |
| `EMBEDDING_MODEL`      | `text-embedding-3-large`                                   | No       | OpenAI embedding model (3072 dims)                  |
| `CATEGORY_MODEL`       | `gpt-4o-mini`                                              | No       | Chat model used to name recipe clusters             |

---

## API reference

| Method | Path          | Purpose                          | Key params                      | Rate tier   |
| ------ | ------------- | -------------------------------- | ------------------------------- | ----------- |
| `POST` | `/url`        | Extract a recipe from a URL      | body: `{ "url": "..." }`        | expensive   |
| `GET`  | `/search`     | Semantic free-text search        | `q` (1–500), `limit` (1–50)     | expensive   |
| `GET`  | `/recipes`    | List recipes (cursor paginated)  | `limit` (1–50), `cursor`, `category` | read   |
| `GET`  | `/categories` | List all categories              | —                               | read        |
| `GET`  | `/similar`    | Recipes similar to a given URL   | `url`, `limit` (1–20)           | read        |
| `GET`  | `/`           | Health check                     | —                               | unlimited   |
| `GET`  | `/ping`       | Health check                     | —                               | unlimited   |

When a rate limit is exceeded, the API responds with **HTTP 429** and a **`Retry-After`**
header (seconds until the client may retry).

### Examples

**Extract a recipe:**

```bash
curl -X POST http://localhost:8000/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/recipes/pancakes"}'
```

```jsonc
{
  "title": "Fluffy Pancakes",
  "source_url": "https://example.com/recipes/pancakes",
  "image_url": "https://example.com/img/pancakes.jpg",
  "prep_time": "10 min",
  "cook_time": "15 min",
  "total_time": "25 min",
  "servings": "4",
  "category": "Breakfast & Brunch",
  "ingredients": [
    { "raw": "2 cups flour", "name": "flour", "quantity": 2, "quantity_max": null, "unit": "cup", "scalable": true }
  ],
  "instructions": ["Whisk dry ingredients.", "Fold in wet ingredients.", "Cook on a griddle."]
}
```

**List recipes with pagination:**

```bash
curl "http://localhost:8000/recipes?limit=20&category=3"
```

```jsonc
{
  "items": [
    {
      "title": "Fluffy Pancakes",
      "source_url": "https://example.com/recipes/pancakes",
      "image_url": "https://example.com/img/pancakes.jpg",
      "prep_time": "10 min",
      "cook_time": "15 min",
      "total_time": "25 min",
      "servings": "4",
      "category": "Breakfast & Brunch"
    }
  ],
  "next_cursor": "eyJ..."  // pass back as ?cursor= for the next page; null when exhausted
}
```

**Search:**

```bash
curl "http://localhost:8000/search?q=spicy%20thai%20noodles&limit=10"
```

---

## Rate limiting

Rate limiting is enforced per client IP via [slowapi](https://github.com/laurentS/slowapi)
(`middleware/rate_limiter.py`). Two tiers keep the public API usable while blocking abuse:

- **Expensive** (`RATE_LIMIT_EXPENSIVE`, default `30/hour`) — `POST /url`, `GET /search`.
  These call OpenAI, so they're kept strict.
- **Read** (`RATE_LIMIT_READ`, default `60/minute`) — `/recipes`, `/categories`, `/similar`.
  Cheap DB reads; generous enough for normal browsing, tight enough to stop bulk scraping.
- Health endpoints (`/`, `/ping`) are unlimited.

Client IP is resolved from the first `X-Forwarded-For` entry (behind the Azure Container Apps
ingress), falling back to the socket peer.

> **Scaling caveat:** limits are stored **in-memory per process**. Under autoscaling the
> effective limit is `value × replica count`. To share limits across replicas, pass
> `storage_uri="redis://..."` to the `Limiter(...)` — no other code changes needed.

---

## Data model & migrations

Two main tables:

- **`recipes`** — structured columns (`title`, `image_url`, `prep_time`, `cook_time`,
  `total_time`, `servings`, `ingredients` JSONB, `instructions` JSONB, `created_at`) plus an
  `embedding vector(3072)` column for pgvector similarity.
- **`categories`** — `id`, `name`, `description`, and a `centroid` embedding. This table is
  (re)built by `scripts/build_categories.py`, which truncates and repopulates it from the
  latest clustering run.

The `recipes` schema is evolved by the ordered SQL in `db/migrations/` (`001` → `005`), applied
in numeric order. These migrations mutate an existing `recipes` table rather than creating the
schema from scratch, and `005` resizes the embedding column to 3072 dims for
`text-embedding-3-large`.

---

## Maintenance scripts

Run these from the `backend/` directory with the virtualenv active.

| Script                            | What it does                                                                 | Run                                 |
| --------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------- |
| `scripts/seed.py`                 | Bulk-ingest recipes from `scripts/recipes.txt` (bypasses the API rate limit) | `python scripts/seed.py`            |
| `scripts/backfill_embeddings.py`  | Generate embeddings for rows where `embedding IS NULL` (batched to OpenAI)    | `python scripts/backfill_embeddings.py` |
| `scripts/build_categories.py`     | Rebuild the category taxonomy: cluster embeddings (UMAP → K-Means) and name clusters with an LLM | `python scripts/build_categories.py` |

---

## Testing

```bash
pytest
```

The suite covers ingredient parsing (`tests/test_ingredient_parser.py`), pagination cursors
(`tests/test_pagination.py`), categories (`tests/test_categories.py`), and rate limiting
(`tests/test_rate_limit.py`).

---

## Deployment

Deployment is automated via GitHub Actions (`.github/workflows/deploy.yml`). On every push to
`main` that touches `backend/**`:

1. **Test** — installs deps and runs `pytest backend/tests/`.
2. **Build & push** — builds the Docker image and pushes it to Azure Container Registry
   `dashcookacr` (tags: commit SHA + `latest`).
3. **Deploy** — deploys the image to the Azure Container App `dashcook-api` in resource group
   `dashcook-rg`.

The container runs a single Uvicorn process (`CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`).

To update non-secret config (e.g. rate limits) on the running app without a code change:

```bash
az containerapp update \
  --name dashcook-api \
  --resource-group dashcook-rg \
  --set-env-vars RATE_LIMIT_EXPENSIVE=30/hour RATE_LIMIT_READ=60/minute
```
