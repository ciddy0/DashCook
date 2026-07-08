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
-- `centroid` is NULL for the catch-all ("Other") row, which collects recipes that fall
-- outside every real cluster's `radius` (the membership distance cutoff, in cosine space).
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    centroid    vector(3072),
    radius      DOUBLE PRECISION,
    is_catchall BOOLEAN NOT NULL DEFAULT FALSE
);

-- Idempotent upgrades for pre-existing `categories` tables (no migration system).
ALTER TABLE categories ADD COLUMN IF NOT EXISTS radius DOUBLE PRECISION;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS is_catchall BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE categories ALTER COLUMN centroid DROP NOT NULL;

-- Support tickets (see db/migrations/006_tickets.sql). `submitter_ip_hash` is a
-- salted SHA-256 of the client IP for abuse correlation — never the raw address.
CREATE TABLE IF NOT EXISTS tickets (
    id                UUID PRIMARY KEY,
    category          TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'open',
    subject           TEXT NOT NULL,
    description       TEXT NOT NULL,
    recipe_url        TEXT,
    metadata          JSONB NOT NULL DEFAULT '{}',
    submitter_ip_hash TEXT,
    user_agent        TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets (created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets (category);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status);
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
