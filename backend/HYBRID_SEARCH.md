# Hybrid Search

## Overview

DashCook uses hybrid search to find recipes by combining **keyword matching** (PostgreSQL full-text search) with **semantic similarity** (pgvector cosine distance). This solves a key limitation of vector-only search: exact keyword matches (e.g. a specific ingredient name or dish title) could be ranked poorly if the embedding didn't capture them well.

The pipeline has three layers:

1. **PostgreSQL FTS** — keyword relevance via `tsvector`/`tsquery`
2. **pgvector** — semantic similarity via OpenAI embeddings
3. **Reciprocal Rank Fusion (RRF)** — merges the two ranked lists into one score
4. **Cohere reranking** (optional) — a neural reranker refines the final order

## Architecture

```
User query
    │
    ├──► embed_query() ──► pgvector cosine search (top 50)  ─┐
    │                                                         ├──► RRF fusion ──► (optional) Cohere rerank ──► response
    └──► websearch_to_tsquery() ──► FTS ts_rank (top 50)   ──┘
```

## How It Works

### 1. Full-Text Search (FTS)

A `tsvector` column (`fts`) on the `recipes` table stores pre-computed search tokens. It is built from:

- **Title** — weight `A` (highest priority)
- **Ingredient names** — weight `B`

A trigger (`trg_recipes_fts`) automatically keeps this column in sync on `INSERT` or `UPDATE` of `title`/`ingredients`. A GIN index (`idx_recipes_fts`) accelerates lookups.

The query is parsed with `websearch_to_tsquery('english', ...)`, which supports natural search syntax (e.g. `"chicken parmesan" -gluten`). Results are ranked by `ts_rank`.

**Migration:** `db/migrations/006_add_fts.sql`

### 2. Vector Search

Each recipe has an `embedding` column (populated via OpenAI `text-embedding-3-large`). At query time the user's search string is embedded with the same model, and pgvector's `<=>` operator computes cosine distance to find the nearest neighbors.

### 3. Reciprocal Rank Fusion (RRF)

Both retrieval methods independently return their top 50 results, each assigned a rank via `ROW_NUMBER()`. A `FULL OUTER JOIN` on `url` merges them, and each result gets a combined score:

```
score = 1/(60 + rank_vector) + 1/(60 + rank_text)
```

- Results found by **both** methods get contributions from both terms.
- Results found by **only one** method get a single term (the other defaults to 0).
- The constant `60` (the standard RRF _k_ parameter) dampens the influence of high ranks so that a result ranked #1 doesn't overwhelm the fusion.

The merged list is sorted by `score DESC` and truncated to the requested limit.

**Implementation:** `db/recipes.py` — `hybrid_search_recipes()`

### 4. Cohere Reranking (optional)

When the caller passes `rerank=true`, the RRF results (up to 50) are sent to Cohere's `rerank-english-v3.0` model. The reranker scores each result against the original query using a cross-encoder, producing more accurate relevance scores than the lightweight RRF heuristic.

Behavior:

- If `COHERE_API_KEY` is not set, reranking is silently skipped and RRF results are returned as-is.
- If the Cohere API call fails at runtime, the service logs a warning and falls back to RRF order.

**Implementation:** `services/search_service.py` — `rerank_results()`

## API Usage

### `GET /recipes/search`

| Parameter | Type   | Default | Description                           |
|-----------|--------|---------|---------------------------------------|
| `q`       | string | —       | Free-text search query (1–500 chars)  |
| `limit`   | int    | 10      | Max results to return (1–50)          |
| `rerank`  | bool   | false   | Enable Cohere neural reranking        |

**Example request:**

```
GET /recipes/search?q=spicy chicken tacos&limit=5
```

**Example response:**

```json
[
  {
    "title": "Spicy Chicken Tacos",
    "source_url": "https://example.com/spicy-chicken-tacos",
    "image_url": "https://example.com/img/tacos.jpg",
    "score": 0.0322
  }
]
```

When `rerank=true`, the `score` field contains the Cohere relevance score (0–1) instead of the RRF score.

**Error:** Returns `503` if the embedding service is unreachable.

## Configuration

| Environment Variable | Required | Purpose                              |
|----------------------|----------|--------------------------------------|
| `OPENAI_API_KEY`     | Yes      | Generates query embeddings           |
| `COHERE_API_KEY`     | No       | Enables neural reranking when set    |

## Files Involved

| File                            | Role                                               |
|---------------------------------|----------------------------------------------------|
| `db/migrations/006_add_fts.sql` | Adds `fts` column, GIN index, trigger, and backfill |
| `db/recipes.py`                 | `hybrid_search_recipes()` — RRF SQL query          |
| `services/search_service.py`    | `rerank_results()` — Cohere reranking with fallback |
| `services/embedder.py`          | `embed_query()` — OpenAI embedding for the query   |
| `routes/recipes.py`             | `/search` endpoint wiring                          |
| `config.py`                     | `cohere_api_key` setting                           |
| `models/recipes.py`             | `SimilarRecipe` response model                     |
