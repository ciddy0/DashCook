from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://dashcook:dashcook@localhost:5433/dashcook"
    supabase_url: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    rate_limit: int = 30
    ollama_host: str = "http://localhost:11434"
    embedding_model: str = "qwen3-embedding:4b"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
