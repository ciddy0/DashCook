import asyncpg
from fastapi import HTTPException

from utils.url import normalize_url, validate_url
from db.recipes import get_cached_recipe, cache_recipe
from services.scraper import fetch_page
from services.parser import parse_recipe
from models.recipes import Recipe
from services.embedder import generate_embedding

async def extract_recipe(pool: asyncpg.Pool, raw_url: str) -> Recipe:
    url = normalize_url(raw_url)

    try:
        validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cached = await get_cached_recipe(pool, url)
    if cached is not None:
        return Recipe(**cached)

    try:
        html = await fetch_page(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"failed to fetch URL D: {e}")

    try:
        recipe_data = parse_recipe(html)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    embedding = await generate_embedding(recipe_data)
    await cache_recipe(pool, url, recipe_data, embedding)

    return Recipe(source_url=url, **recipe_data)
