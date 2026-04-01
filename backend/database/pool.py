import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS recipe_cache (
    url        TEXT PRIMARY KEY,
    recipe     JSONB NOT NULL,
    cached_at  TIMESTAMPTZ DEFAULT NOW()
)
"""


async def create_pool() -> asyncpg.Pool:
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)
    return pool
