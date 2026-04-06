import json

import asyncpg
from pydantic import BaseModel

from database.pool import SCHEMA_VERSION


class _PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


async def get_cached_recipe(pool: asyncpg.Pool, url: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT recipe FROM recipe_cache WHERE url = $1", url
        )
    if row is None:
        return None
    return json.loads(row["recipe"])


async def cache_recipe(pool: asyncpg.Pool, url: str, recipe_data: dict) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO recipe_cache (url, recipe, schema_ver)
            VALUES ($1, $2, $3)
            ON CONFLICT (url) DO NOTHING
            """,
            url,
            json.dumps(recipe_data, cls=_PydanticEncoder),
            SCHEMA_VERSION,
        )
