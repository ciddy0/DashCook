-- Run once to migrate existing data
ALTER TABLE recipes
    ADD COLUMN IF NOT EXISTS title        TEXT,
    ADD COLUMN IF NOT EXISTS image_url    TEXT,
    ADD COLUMN IF NOT EXISTS prep_time    TEXT,
    ADD COLUMN IF NOT EXISTS cook_time    TEXT,
    ADD COLUMN IF NOT EXISTS total_time   TEXT,
    ADD COLUMN IF NOT EXISTS servings     TEXT,
    ADD COLUMN IF NOT EXISTS ingredients  JSONB,
    ADD COLUMN IF NOT EXISTS instructions JSONB,
    ADD COLUMN IF NOT EXISTS created_at   TIMESTAMPTZ DEFAULT NOW();

-- Backfill from existing JSONB blob
UPDATE recipes SET
    title        = data->>'title',
    image_url    = data->>'image_url',
    prep_time    = data->>'prep_time',
    cook_time    = data->>'cook_time',
    total_time   = data->>'total_time',
    servings     = data->>'servings',
    ingredients  = data->'ingredients',
    instructions = data->'instructions'
WHERE data IS NOT NULL;

-- Set NOT NULL constraints after backfill
ALTER TABLE recipes
    ALTER COLUMN title        SET NOT NULL,
    ALTER COLUMN ingredients  SET NOT NULL,
    ALTER COLUMN instructions SET NOT NULL;

-- Create index
CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes (title);

-- Drop old blob column
ALTER TABLE recipes DROP COLUMN IF EXISTS data;
