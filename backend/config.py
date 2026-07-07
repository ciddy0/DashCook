from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://dashcook:dashcook@localhost:5433/dashcook"
    supabase_url: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    rate_limit_expensive: str = "30/hour"
    rate_limit_read: str = "60/minute" 
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-large"
    category_model: str = "gpt-4o-mini" 

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
