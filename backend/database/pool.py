import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS recipe_cache (
    url          TEXT PRIMARY KEY,
    recipe       JSONB NOT NULL,
    cached_at    TIMESTAMPTZ DEFAULT NOW(),
    schema_ver   INT NOT NULL DEFAULT 1
)
"""

# Bump this whenever the stored JSONB shape changes (e.g. ingredients schema update).
SCHEMA_VERSION = 2

MIGRATE_SQL = """
DO $$
BEGIN
    -- add schema_ver column if it doesn't exist yet (first migration)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'recipe_cache' AND column_name = 'schema_ver'
    ) THEN
        ALTER TABLE recipe_cache ADD COLUMN schema_ver INT NOT NULL DEFAULT 1;
    END IF;
END
$$;
DELETE FROM recipe_cache WHERE schema_ver < {ver};
"""


async def create_pool() -> asyncpg.Pool:
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)
        await conn.execute(MIGRATE_SQL.format(ver=SCHEMA_VERSION))
    return pool
