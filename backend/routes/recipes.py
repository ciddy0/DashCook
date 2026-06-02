from fastapi import APIRouter, HTTPException, Query

from dependencies import DbPool
from models.requests import ExtractRequest
from models.recipes import Recipe
from models.recipes import SimilarRecipe
from services.recipe_service import extract_recipe
from db.recipes import get_similar_recipes, search_recipes
from services.embedder import embed_query

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

@router.get("/search", response_model=list[SimilarRecipe])
async def search(
    pool: DbPool,
    q: str = Query(..., min_length=1, description="Free-text recipe search query"),
    limit: int = Query(10, ge=1, le=50),
):
    try:
        query_embedding = await embed_query(q)
    except Exception:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")
    return await search_recipes(pool, query_embedding, limit)