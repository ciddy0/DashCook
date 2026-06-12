-- Add tsvector column for full-text search (not generated — triggers keep it in sync)
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS fts tsvector;

CREATE INDEX IF NOT EXISTS idx_recipes_fts ON recipes USING GIN (fts);

-- Trigger function: builds tsvector from title (weight A) + ingredient names (weight B)
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

-- Backfill existing rows
UPDATE recipes SET fts =
  setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
  setweight(to_tsvector('english', coalesce(
    (SELECT string_agg(elem->>'name', ' ')
     FROM jsonb_array_elements(ingredients) AS elem), ''
  )), 'B');
