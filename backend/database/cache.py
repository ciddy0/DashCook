import json

import asyncpg
from pydantic import BaseModel

class _PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

async def get_cached_recipe(pool, url: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT data FROM recipes WHERE url = $1",
            url
        )
        return json.loads(row["data"]) if row else None

async def cache_recipe(pool, url: str, recipe_data: dict):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO recipes (url, data)
            VALUES ($1, $2)
            ON CONFLICT (url)
            DO UPDATE SET data = EXCLUDED.data
            """,
            url,
            json.dumps(recipe_data, cls=_PydanticEncoder)
        )
