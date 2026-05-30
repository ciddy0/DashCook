from fastapi import APIRouter

from dependencies import DbPool
from models.requests import ExtractRequest
from models.recipes import Recipe
from services.recipe_service import extract_recipe

router = APIRouter()


@router.post("/url", response_model=Recipe)
async def get_recipe(body: ExtractRequest, pool: DbPool):
    return await extract_recipe(pool, str(body.url))
