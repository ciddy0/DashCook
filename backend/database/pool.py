import os

import asyncpg
from dotenv import load_dotenv

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS recipes (
    url          TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    image_url    TEXT,
    prep_time    TEXT,
    cook_time    TEXT,
    total_time   TEXT,
    servings     TEXT,
    ingredients  JSONB NOT NULL DEFAULT '[]',
    instructions JSONB NOT NULL DEFAULT '[]',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes (title);
"""


async def create_pool():
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")

    if supabase_url:
        pool = await asyncpg.create_pool(
            dsn=supabase_url,
            ssl="require",
            min_size=1,
            max_size=10,
        )
        print("Connected to Supabase (production)")
        return pool

    local_url = os.getenv("DATABASE_URL", "postgresql://dashcook:dashcook@localhost:5433/dashcook")
    pool = await asyncpg.create_pool(dsn=local_url, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)
    print("Connected to local PostgreSQL (development)")
    return pool
