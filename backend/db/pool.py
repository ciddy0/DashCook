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
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fts          tsvector
);

CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes (title);
CREATE INDEX IF NOT EXISTS idx_recipes_fts ON recipes USING GIN (fts);

CREATE OR REPLACE FUNCTION recipes_fts_update() RETURNS trigger AS $$
BEGIN
  NEW.fts :=
    setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(
      (SELECT string_agg(elem->>'name', ' ')
       FROM jsonb_array_elements(NEW.ingredients) AS elem), ''
    )), 'B');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_recipes_fts ON recipes;
CREATE TRIGGER trg_recipes_fts
  BEFORE INSERT OR UPDATE OF title, ingredients ON recipes
  FOR EACH ROW EXECUTE FUNCTION recipes_fts_update();
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
