import json

from pydantic import BaseModel


class _PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

async def get_cached_recipe(pool, url: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM recipes WHERE url = $1", url)
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
            "ingredients": json.loads(row["ingredients"]),
            "instructions": json.loads(row["instructions"]),
        }

async def cache_recipe(
    pool, url: str, recipe_data: dict, embedding: list[float] | None = None
):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO recipes (url, title, image_url, prep_time, cook_time, total_time, servings, ingredients, instructions, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (url) DO UPDATE SET
                title        = EXCLUDED.title,
                image_url    = EXCLUDED.image_url,
                prep_time    = EXCLUDED.prep_time,
                cook_time    = EXCLUDED.cook_time,
                total_time   = EXCLUDED.total_time,
                servings     = EXCLUDED.servings,
                ingredients  = EXCLUDED.ingredients,
                instructions = EXCLUDED.instructions,
                embedding    = COALESCE(EXCLUDED.embedding, recipes.embedding)
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
        )

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