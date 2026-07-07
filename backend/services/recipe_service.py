import logging

import asyncpg
from fastapi import HTTPException

logger = logging.getLogger(__name__)

from utils.url import normalize_url, validate_url
from db.recipes import get_cached_recipe, cache_recipe
from db.categories import assign_category
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
        logger.error("Failed to fetch URL %s: %s", url, e)
        raise HTTPException(status_code=422, detail="Failed to fetch URL")

    try:
        recipe_data = parse_recipe(html)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    embedding = await generate_embedding(recipe_data)

    # Assign the nearest existing category (no-op if no categories exist yet).
    section_id = None
    category_name = None
    assigned = await assign_category(pool, embedding)
    if assigned is not None:
        section_id, category_name = assigned

    await cache_recipe(pool, url, recipe_data, embedding, section_id)

    return Recipe(source_url=url, category=category_name, **recipe_data)
