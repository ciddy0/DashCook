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

On top of that store sit two Claude-backed endpoints: a **RAG discovery** endpoint that turns
a vague craving into real recipes from the database, and a **recipe Q&A** endpoint for
questions about a recipe you're cooking.

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
- **RAG discovery** — "cozy warm dinners" retrieves a shortlist by embedding distance and has
  Claude pick the ones that actually fit, with a line on why each works. Degrades to plain
  semantic search when the daily AI budget is spent.

---

## Features

- 🧹 **Recipe extraction & normalization** from arbitrary recipe pages
- 🥕 **Ingredient parsing** into name / quantity / unit / scalable
- 💾 **DB-backed caching** of extracted recipes
- 🔎 **Semantic search** over recipes (`GET /search`)
- 🧭 **Similar-recipe recommendations** (`GET /similar`)
- 🍲 **RAG recipe discovery** — retrieve, then let Claude pick and explain (`POST /discover`)
- 💬 **Grounded recipe Q&A** — substitutions, timing, storage (`POST /ask`)
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
| Embeddings         | OpenAI (`text-embedding-3-large`, `gpt-4o-mini` for cluster naming) |
| Generation         | Anthropic Claude (`claude-haiku-4-5`) for discovery + recipe Q&A |
| Scraping           | `httpx`, `cloudscraper`, BeautifulSoup                        |
| Rate limiting      | [slowapi](https://github.com/laurentS/slowapi)                |
| Tests              | pytest                                                        |
| Container / deploy | Docker → Azure Container Apps (GitHub Actions)                |

---

## Architecture

### Extraction

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

### RAG discovery

`POST /discover` answers "what should I cook" queries. Embedding search does the **retrieval**,
Claude does the **generation**, and a validation step keeps the generation tied to what was
actually retrieved:

```
POST /discover  { "query": "cozy warm dinners", "limit": 5 }
      │
      ▼
  embed_query (OpenAI, 3072-dim) ──── fails ────► 503
      │                                           the one hard failure:
      │                                           no shortlist, nothing to show
      ▼
  search_recipes_detailed (pgvector)                 [ RETRIEVE ]
      │   20 nearest recipes by cosine distance
      │   title · times · servings · category · ingredients
      │
      ▼
  daily AI budget left? ─────────── no ──────────────┐
      │ yes                                          │
      ▼                                              │
  pick_recipes (Claude Haiku 4.5) ──── error ────────┤   [ GENERATE ]
      │   in:  the 20 as a numbered list + the query │
      │   out: { intro, picks: [{ id, why }] }       │
      │        (structured output, json_schema)      │
      ▼                                              │
  _validate_picks ──────── nothing survives ─────────┤   [ GROUND ]
      │   every id must name a row from the          │
      │   shortlist above; unknown, duplicate and    │
      │   malformed picks are dropped                │
      ▼                                              ▼
  consume() one request from the budget         FALLBACK
      │                                              │
      ▼                                              ▼
  mode: "ai"                                    mode: "search"
  intro + a "why" line per recipe               top 5 by distance, no prose
```

Three properties worth noting:

- **Nothing is invented.** Claude only ever sees recipes that came out of pgvector, refers to
  them by number, and every number it returns is checked back against that shortlist. A recipe
  that isn't in the database cannot reach the response — which also caps the blast radius of a
  prompt injection hidden in a scraped recipe title.
- **Every failure degrades instead of erroring.** No budget, no API key, Claude down, or nothing
  on the shortlist fitting — all four return the same response shape with `mode: "search"`.
  The client renders one list either way.
- **The budget is spent on success only.** `consume()` runs after Claude has delivered, so an
  outage never costs a user one of their daily requests.

---

## Project structure

```
backend/
├── main.py                 # FastAPI app: lifespan, CORS, rate-limit wiring, routers
├── config.py               # Pydantic settings (env-driven)
├── dependencies.py         # Shared FastAPI dependencies (DB pool injection)
├── routes/                 # HTTP endpoints
│   ├── recipes.py          #   /url, /recipes, /categories, /similar, /search, /ask, /discover
│   ├── tickets.py          #   /tickets
│   └── health.py           #   /, /ping
├── services/               # Business logic
│   ├── recipe_service.py   #   extraction orchestration
│   ├── scraper.py          #   page fetching (per-domain throttling)
│   ├── parser.py           #   HTML → structured recipe
│   ├── ingredient_parser.py#   ingredient string → name/quantity/unit
│   ├── embedder.py         #   OpenAI embeddings
│   ├── recipe_qa.py        #   Claude Q&A grounded in one recipe
│   └── recipe_discovery.py #   Claude picks from a retrieved shortlist (RAG)
├── db/                     # Data access
│   ├── pool.py             #   asyncpg connection pool
│   ├── recipes.py          #   recipe queries (cache, list, search, similar)
│   ├── categories.py       #   category queries + assign_category
│   └── migrations/         #   ordered SQL migrations
├── models/                 # Pydantic request/response models
├── middleware/
│   ├── rate_limiter.py     # slowapi Limiter (per-IP, X-Forwarded-For aware)
│   └── ai_quota.py         # shared daily budget across the Claude endpoints
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
ANTHROPIC_API_KEY=sk-ant-...
RATE_LIMIT_EXPENSIVE=30/hour
RATE_LIMIT_READ=60/minute
RATE_LIMIT_AI=5/day
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
| `ANTHROPIC_API_KEY`    | `""`                                                       | No*      | Claude key for `/ask` + `/discover`                 |
| `QA_MODEL`             | `claude-haiku-4-5`                                         | No       | Model behind `POST /ask`                            |
| `DISCOVER_MODEL`       | `claude-haiku-4-5`                                         | No       | Model behind `POST /discover`                       |
| `RATE_LIMIT_AI`        | `5/day`                                                    | No       | Shared daily budget across `/ask` and `/discover`   |
| `RATE_LIMIT_TICKET`    | `2/minute;5/hour`                                          | No       | Aggressive per-IP limit for `POST /tickets`         |
| `ADMIN_TOKEN`          | `""`                                                       | No*      | Secret for `GET /tickets`; unset ⇒ that endpoint returns 503 |
| `IP_HASH_SALT`         | `""`                                                       | No       | Salt for hashing submitter IPs; unset ⇒ hash stored as NULL |
| `MAX_REQUEST_BODY_BYTES` | `16384`                                                 | No       | Reject request bodies larger than this with 413     |

\* `ADMIN_TOKEN` is only required to use the owner-only `GET /tickets` endpoint. Generate one with
`python -c "import secrets; print(secrets.token_urlsafe(32))"`.

\* `ANTHROPIC_API_KEY` is only required for the Claude endpoints. Without it both fail closed:
`POST /ask` returns 503, and `POST /discover` quietly serves plain semantic search results.

---

## API reference

| Method | Path          | Purpose                          | Key params                      | Rate tier   |
| ------ | ------------- | -------------------------------- | ------------------------------- | ----------- |
| `POST` | `/url`        | Extract a recipe from a URL      | body: `{ "url": "..." }`        | expensive   |
| `GET`  | `/search`     | Semantic free-text search        | `q` (1–500), `limit` (1–50)     | expensive   |
| `POST` | `/discover`   | RAG discovery: retrieve → Claude picks | body: `{ "query", "limit" }` | expensive + AI |
| `POST` | `/ask`        | Q&A about a recipe (Claude)      | body: recipe + `question`       | expensive + AI |
| `GET`  | `/recipes`    | List recipes (cursor paginated)  | `limit` (1–50), `cursor`, `category` | read   |
| `GET`  | `/categories` | List all categories              | —                               | read        |
| `GET`  | `/similar`    | Recipes similar to a given URL   | `url`, `limit` (1–20)           | read        |
| `POST` | `/tickets`    | Submit a support ticket (public) | body: see below                 | ticket      |
| `GET`  | `/tickets`    | List tickets (**owner only**)    | `limit`, `offset`, `category`, `status`, `search` | read |
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

**Discover recipes for a mood (RAG):**

```bash
curl -X POST http://localhost:8000/discover \
  -H "Content-Type: application/json" \
  -d '{"query": "cozy warm dinners", "limit": 5}'
```

```jsonc
{
  "mode": "ai",                  // "search" when it fell back — see Architecture
  "answer": "For a cozy night in, these all lean slow-cooked and rich:",
  "recipes": [
    {
      "title": "Beef Bourguignon",
      "source_url": "https://example.com/beef-bourguignon",
      "image_url": "https://example.com/img/beef.jpg",
      "total_time": "3 hours",
      "why": "Braises for three hours in red wine — about as warming as dinner gets."
    }
  ],
  "remaining": 4                 // AI requests this client has left today
}
```

In fallback mode (`"mode": "search"`) the shape is identical, with `answer` and every `why`
set to `null`. Clients should render the list either way rather than treating it as an error.

**Ask about a recipe:**

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
        "question": "Can I use oil instead of butter?",
        "title": "Fluffy Pancakes",
        "servings": "4",
        "ingredients": ["2 cups flour", "3 tbsp butter, melted"],
        "instructions": ["Whisk dry ingredients.", "Cook on a griddle."],
        "history": []
      }'
```

The client supplies the recipe context (so freshly extracted recipes work before they're in the
database) and up to 8 prior `{ question, answer }` turns for follow-ups. Returns
`{ "answer": "..." }`, or **429** once the shared daily budget is gone.

**Submit a support ticket (public):**

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
        "category": "parser",
        "subject": "Recipe parser failed",
        "description": "The recipe at example.com/x did not parse.",
        "recipe_url": "https://example.com/x"
      }'
```

`category` is one of `parser`, `recipe`, `account`, `bug`, `feature_request`, `other`.
`recipe_url` and `metadata` (a JSON object) are optional. The response is a minimal
acknowledgement — `{ "id", "status", "created_at" }` — and does not echo the submitted content.

**List tickets (owner only):**

```bash
curl "http://localhost:8000/tickets?status=open&category=parser&search=fail&limit=20&offset=0" \
  -H "X-Admin-Token: $ADMIN_TOKEN"
```

Newest first. Returns `{ "items": [...], "total", "limit", "offset" }`. Without a valid
`X-Admin-Token` the endpoint returns **401**; if `ADMIN_TOKEN` is unset it returns **503**.

---

## Rate limiting

Rate limiting is enforced per client IP via [slowapi](https://github.com/laurentS/slowapi)
(`middleware/rate_limiter.py`). Tiered limits keep the public API usable while blocking abuse:

- **Expensive** (`RATE_LIMIT_EXPENSIVE`, default `30/hour`) — `POST /url`, `GET /search`,
  `POST /discover`, `POST /ask`. These call OpenAI or Anthropic, so they're kept strict.
- **Read** (`RATE_LIMIT_READ`, default `60/minute`) — `/recipes`, `/categories`, `/similar`,
  `GET /tickets`. Cheap DB reads; generous for browsing, tight enough to stop bulk scraping.
- **Ticket** (`RATE_LIMIT_TICKET`, default `2/minute;5/hour`) — `POST /tickets`. Deliberately
  aggressive: the `2/minute` burst cap stops rapid spam, the `5/hour` cap stops sustained abuse.
- Health endpoints (`/`, `/ping`) are unlimited.

Requests larger than `MAX_REQUEST_BODY_BYTES` (default 16 KB) are rejected with **413** before
any handler runs, and unhandled server errors return a generic **500** without leaking internals.

Client IP is resolved from the first `X-Forwarded-For` entry (behind the Azure Container Apps
ingress), falling back to the socket peer.

> **Scaling caveat:** limits are stored **in-memory per process**. Under autoscaling the
> effective limit is `value × replica count`, and a replica that scales to zero on idle loses
> its counters entirely. To share limits across replicas, pass `storage_uri="redis://..."` to
> the `Limiter(...)` — no other code changes needed.

### The AI budget

Claude calls cost real money per request, so `/ask` and `/discover` sit behind a second,
stricter limit on top of the expensive tier: a **shared daily budget** (`RATE_LIMIT_AI`,
default `5/day`) implemented in `middleware/ai_quota.py`. Both endpoints draw from one pool
keyed by client IP, so a visitor gets one allowance per day rather than one per feature.

Two deliberate differences from the decorator-based tiers above:

- **Charged on success.** Both endpoints check the budget up front but only `consume()` after
  Claude has actually answered, so an API outage never costs a user one of their requests.
  The expensive-tier decorator is what bounds retries in the meantime.
- **Exhaustion isn't always an error.** `/ask` returns **429**; `/discover` returns **200**
  with `mode: "search"` and plain semantic results.

The budget uses the same in-memory storage as the tiers above, so the scaling caveat applies
here too — and it bites harder, since a day-long window has far more time to be interrupted by
a deploy or an idle scale-to-zero than a per-minute one. Moving to Redis, or a small Postgres
counter table, is the fix if the limit ever needs to be exact.

---

## Data model & migrations

Three main tables:

- **`recipes`** — structured columns (`title`, `image_url`, `prep_time`, `cook_time`,
  `total_time`, `servings`, `ingredients` JSONB, `instructions` JSONB, `created_at`) plus an
  `embedding vector(3072)` column for pgvector similarity.
- **`categories`** — `id`, `name`, `description`, and a `centroid` embedding. This table is
  (re)built by `scripts/build_categories.py`, which truncates and repopulates it from the
  latest clustering run.
- **`tickets`** — support tickets (`id` UUID, `category`, `status`, `subject`, `description`,
  `recipe_url`, `metadata` JSONB, `submitter_ip_hash`, `user_agent`, `created_at`,
  `updated_at`). **Privacy:** the raw client IP is never stored — only a salted SHA-256 hash
  (`IP_HASH_SALT`), which lets the owner spot repeat abuse from one source without retaining
  personal data. If no salt is set, the hash is stored as `NULL`.

The `recipes` schema is evolved by the ordered SQL in `db/migrations/` (`001` → `006`), applied
in numeric order. `005` resizes the embedding column to 3072 dims for `text-embedding-3-large`;
`006` creates the `tickets` table. The `tickets` DDL is also bootstrapped at startup for local
dev (`db/pool.py`), but **production/Supabase skips startup DDL**, so run `006` there manually:

```bash
psql "$SUPABASE_URL" -f db/migrations/006_tickets.sql
```

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
(`tests/test_pagination.py`), categories (`tests/test_categories.py`), rate limiting
(`tests/test_rate_limit.py`), tickets (`tests/test_tickets.py`), and RAG discovery
(`tests/test_discovery.py`).

`test_discovery.py` stubs the embedding and Claude calls and asserts the behaviour that's easy
to regress: every fallback path returns results rather than an error, a failed Claude call
doesn't spend the budget, `/ask` and `/discover` share one counter, and `_validate_picks` drops
ids that aren't on the retrieved shortlist. **No test makes a live Claude call** — the
structured-output contract itself is only exercised against the real API.

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
