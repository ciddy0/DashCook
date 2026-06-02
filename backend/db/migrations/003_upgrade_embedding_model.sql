-- Upgrade embedding column from vector(1024) to vector(4096)
-- for qwen3-embedding:8b model (was qwen3-embedding:0.6b)

-- Widen the column to accept 4096-dim vectors
ALTER TABLE recipes
    ALTER COLUMN embedding TYPE vector(4096);

-- Clear old embeddings since they're from the 0.6b model
-- and incompatible with the 8b model's dimensions
UPDATE recipes SET embedding = NULL;
