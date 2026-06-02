from fastapi import APIRouter, HTTPException, Query

from dependencies import DbPool
from models.requests import ExtractRequest
from models.recipes import Recipe
from models.recipes import SimilarRecipe
from services.recipe_service import extract_recipe
from db.recipes import get_similar_recipes

router = APIRouter()


@router.post("/url", response_model=Recipe)
async def get_recipe(body: ExtractRequest, pool: DbPool):
    return await extract_recipe(pool, str(body.url))


@router.get("/url/{url:path}/similar", response_model=list[SimilarRecipe])
async def similar_recipes(
    url: str,
    pool: DbPool,
    limit: int = Query(5, ge=1, le=20),
):
    results = await get_similar_recipes(pool, url, limit)
    if results is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found or has no embedding",
        )
    return results