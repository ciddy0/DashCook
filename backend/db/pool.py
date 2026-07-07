import asyncpg
from pgvector.asyncpg import register_vector

from config import get_settings

CREATE_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

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
    embedding    vector(3072),
    section_id   INTEGER,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes (title);
CREATE INDEX IF NOT EXISTS idx_recipes_created_at ON recipes (created_at DESC, url DESC);

-- Named recipe categories. `recipes.section_id` references categories.id (kept as a
-- plain INTEGER, no FK, to avoid altering the existing column). Populated occasionally
-- by scripts/build_categories.py; each new recipe is assigned the nearest centroid.
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    centroid    vector(3072) NOT NULL
);
"""


async def _init_connection(conn):
    await register_vector(conn)

async def create_pool():
    settings = get_settings()

    if settings.supabase_url:
        pool = await asyncpg.create_pool(
            dsn=settings.supabase_url,
            ssl="require",
            min_size=1,
            max_size=10,
            init=_init_connection,
        )
        print("Connected to Supabase (production)")
        return pool

    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        await conn.execute(CREATE_TABLE_SQL)
    finally:
        await conn.close()

    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        init=_init_connection,
    )
    print("Connected to local PostgreSQL (development)")
    return pool
