-- Switch from qwen3-embedding:8b (4096 dims) to qwen3-embedding:4b (2560 dims).
-- Existing embeddings are incompatible, so clear them first.

UPDATE recipes SET embedding = NULL;

ALTER TABLE recipes
    ALTER COLUMN embedding TYPE vector(2560);
