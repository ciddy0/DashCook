import json
from datetime import datetime

from pydantic import BaseModel


class _PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

async def get_cached_recipe(pool, url: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT r.*, c.name AS category
            FROM recipes r
            LEFT JOIN categories c ON c.id = r.section_id
            WHERE r.url = $1
            """,
            url,
        )
        if not row:
            return None
        return {
            "title": row["title"],
            "source_url": row["url"],
            "image_url": row["image_url"],
            "prep_time": row["prep_time"],
            "cook_time": row["cook_time"],
            "total_time": row["total_time"],
            "servings": row["servings"],
            "category": row["category"],
            "ingredients": json.loads(row["ingredients"]),
            "instructions": json.loads(row["instructions"]),
        }

async def cache_recipe(
    pool,
    url: str,
    recipe_data: dict,
    embedding: list[float] | None = None,
    section_id: int | None = None,
):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO recipes (url, title, image_url, prep_time, cook_time, total_time, servings, ingredients, instructions, embedding, section_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (url) DO UPDATE SET
                title        = EXCLUDED.title,
                image_url    = EXCLUDED.image_url,
                prep_time    = EXCLUDED.prep_time,
                cook_time    = EXCLUDED.cook_time,
                total_time   = EXCLUDED.total_time,
                servings     = EXCLUDED.servings,
                ingredients  = EXCLUDED.ingredients,
                instructions = EXCLUDED.instructions,
                embedding    = COALESCE(EXCLUDED.embedding, recipes.embedding),
                section_id   = COALESCE(EXCLUDED.section_id, recipes.section_id)
            """,
            url,
            recipe_data["title"],
            recipe_data.get("image_url"),
            recipe_data.get("prep_time"),
            recipe_data.get("cook_time"),
            recipe_data.get("total_time"),
            recipe_data.get("servings"),
            json.dumps(recipe_data["ingredients"], cls=_PydanticEncoder),
            json.dumps(recipe_data["instructions"]),
            embedding,
            section_id,
        )

async def list_recipes(
    pool,
    limit: int = 20,
    cursor_created_at: datetime | None = None,
    cursor_url: str | None = None,
    category_id: int | None = None,
):
    """Keyset-paginated recipe list, newest first, optionally filtered by category.

    Returns (rows, has_more). Fetches limit + 1 rows so the caller can tell
    whether another page exists and build the next cursor from the last kept row.
    """
    # $1 cursor timestamp, $2 cursor url, $3 category filter (NULL = no filter).
    # $4 is limit + 1, appended last.
    params: list = [cursor_created_at, cursor_url, category_id, limit + 1]
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT r.url, r.title, r.image_url, r.prep_time, r.cook_time,
                   r.total_time, r.servings, r.created_at, c.name AS category
            FROM recipes r
            LEFT JOIN categories c ON c.id = r.section_id
            WHERE ($1::timestamptz IS NULL
                   OR (r.created_at, r.url) < ($1::timestamptz, $2::text))
              AND ($3::int IS NULL OR r.section_id = $3::int)
            ORDER BY r.created_at DESC, r.url DESC
            LIMIT $4
            """,
            *params,
        )

    has_more = len(rows) > limit
    return rows[:limit], has_more


async def get_similar_recipes(pool, url: str, limit: int=5):
    async with pool.acquire() as conn:
        # Distinguish "no row" / "null embedding" from "has embedding".
        # fetchval returns None (no row) or a bool (embedding IS NOT NULL).
        has_embedding = await conn.fetchval(
            "SELECT embedding IS NOT NULL FROM recipes WHERE url = $1", url
        )
        if not has_embedding:
            return None

        rows = await conn.fetch(
            """
            SELECT r.title,
                   r.url        AS source_url,
                   r.image_url,
                   r.embedding <=> src.embedding AS distance
            FROM recipes r,
                 (SELECT embedding FROM recipes WHERE url = $1) AS src
            WHERE r.url != $1
              AND r.embedding IS NOT NULL
            ORDER BY r.embedding <=> src.embedding
            LIMIT $2
            """,
            url,
            limit,
        )
        return [
            {
                "title": r["title"],
                "source_url": r["source_url"],
                "image_url": r["image_url"],
                "distance": r["distance"],
            }
            for r in rows
        ]
    
async def search_recipes(
    pool,
    query_embedding: list[float],
    limit: int = 10,
):
    conditions = ["embedding IS NOT NULL"]
    params: list = [query_embedding]  # $1

    params.append(limit)
    limit_placeholder = f"${len(params)}"
    where = " AND ".join(conditions)

    sql = f"""
        SELECT title,
               url AS source_url,
               image_url,
               embedding <=> $1 AS distance
        FROM recipes
        WHERE {where}
        ORDER BY embedding <=> $1
        LIMIT {limit_placeholder}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)

    return [
        {
            "title": r["title"],
            "source_url": r["source_url"],
            "image_url": r["image_url"],
            "distance": r["distance"],
        }
        for r in rows
    ]


def _ingredient_names(raw, limit: int = 10) -> list[str]:
    """Pull the parsed ingredient names out of the stored JSON blob.

    Best-effort: a row with malformed or unexpected ingredient JSON just
    contributes no names rather than failing the whole search.
    """
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []

    names: list[str] = []
    for ing in parsed:
        name = (ing.get("name") or "").strip() if isinstance(ing, dict) else ""
        if name:
            names.append(name)
        if len(names) == limit:
            break
    return names


async def search_recipes_detailed(
    pool,
    query_embedding: list[float],
    limit: int = 20,
):
    """Nearest recipes with enough context for an LLM to rank and describe them.

    search_recipes() returns only what a result card renders; this adds the
    times, servings, category and ingredient names the discovery prompt reasons
    over when picking which recipes actually fit the query.
    """
    sql = """
        SELECT r.title,
               r.url        AS source_url,
               r.image_url,
               r.total_time,
               r.servings,
               r.ingredients,
               c.name       AS category,
               r.embedding <=> $1 AS distance
        FROM recipes r
        LEFT JOIN categories c ON c.id = r.section_id
        WHERE r.embedding IS NOT NULL
        ORDER BY r.embedding <=> $1
        LIMIT $2
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, query_embedding, limit)

    return [
        {
            "title": r["title"],
            "source_url": r["source_url"],
            "image_url": r["image_url"],
            "total_time": r["total_time"],
            "servings": r["servings"],
            "category": r["category"],
            "ingredients": _ingredient_names(r["ingredients"]),
            "distance": r["distance"],
        }
        for r in rows
    ]