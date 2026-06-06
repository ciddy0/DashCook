-- Migrate embedding column from vector(2560) to vector(3072)
-- for OpenAI text-embedding-3-large (was Ollama qwen3-embedding:4b)

-- Clear old embeddings (incompatible dimensions)
UPDATE recipes SET embedding = NULL;

-- Resize column to 3072 dimensions
ALTER TABLE recipes
    ALTER COLUMN embedding TYPE vector(3072);
