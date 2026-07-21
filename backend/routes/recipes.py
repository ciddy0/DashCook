import logging

from fastapi import APIRouter, HTTPException, Query, Request, Response

from config import get_settings
from dependencies import DbPool
from middleware.rate_limiter import limiter
from models.requests import ExtractRequest
from models.recipes import Recipe
from models.recipes import SimilarRecipe
from models.recipes import RecipeCard, RecipeListResponse, Category
from models.qa import RecipeQuestion, RecipeAnswer
from models.discovery import DiscoverRequest, DiscoverResult, DiscoveredRecipe
from services.recipe_service import extract_recipe
from services.recipe_qa import answer_question
from middleware import ai_quota
from services.recipe_discovery import CANDIDATE_POOL, pick_recipes
from db.recipes import (
    get_similar_recipes,
    search_recipes,
    search_recipes_detailed,
    list_recipes,
)
from db.categories import list_categories
from services.embedder import embed_query
from utils.pagination import decode_cursor, encode_cursor

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


@router.post("/url", response_model=Recipe)
@limiter.limit(settings.rate_limit_expensive)
async def get_recipe(request: Request, response: Response, body: ExtractRequest, pool: DbPool):
    return await extract_recipe(pool, str(body.url))


@router.post("/ask", response_model=RecipeAnswer)
@limiter.limit(settings.rate_limit_expensive)
async def ask_recipe(request: Request, response: Response, body: RecipeQuestion):
    """Answer a cooking question about a recipe using Claude.

    Public and unauthenticated, so it draws on the shared daily AI budget
    (settings.rate_limit_ai, also spent by /discover) and fails closed when no
    API key is configured. The decorator above is a coarse backstop: failed
    calls don't spend the daily budget, so something has to bound the retries.
    """
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="The recipe assistant isn't available right now.",
        )
    if not ai_quota.has_budget(request):
        raise HTTPException(
            status_code=429,
            detail="You've used all of today's questions. Check back tomorrow!",
        )
    try:
        answer = await answer_question(
            question=body.question,
            title=body.title,
            servings=body.servings,
            total_time=body.total_time,
            ingredients=body.ingredients,
            instructions=body.instructions,
            history=body.history,
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="The recipe assistant is unavailable right now. Please try again later.",
        )
    if not answer:
        raise HTTPException(
            status_code=502,
            detail="Couldn't come up with an answer. Please try rephrasing.",
        )
    # Only spend the budget once Claude has actually delivered.
    ai_quota.consume(request)
    return RecipeAnswer(answer=answer)


@router.post("/discover", response_model=DiscoverResult)
@limiter.limit(settings.rate_limit_expensive)
async def discover_recipes(
    request: Request, response: Response, body: DiscoverRequest, pool: DbPool
):
    """Answer a "what should I cook" query with recipes from the database.

    Semantic search retrieves a shortlist, then Claude picks the ones that fit
    and says why. Every path that can't produce that — no daily budget left, no
    API key, the assistant erroring, or nothing on the shortlist fitting — falls
    back to plain semantic search results (mode="search") instead of failing, so
    the widget always has something to show.
    """
    try:
        query_embedding = await embed_query(body.query)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Search is unavailable — the embedding service is not reachable",
        )

    candidates = await search_recipes_detailed(pool, query_embedding, CANDIDATE_POOL)

    def _fallback() -> DiscoverResult:
        return DiscoverResult(
            mode="search",
            answer=None,
            recipes=[DiscoveredRecipe(**r) for r in candidates[: body.limit]],
            remaining=ai_quota.remaining(request),
        )

    if not candidates or not settings.anthropic_api_key:
        return _fallback()
    if not ai_quota.has_budget(request):
        return _fallback()

    try:
        intro, picks = await pick_recipes(body.query, candidates, body.limit)
    except Exception as e:
        logger.warning("discovery generation failed, falling back to search: %s", e)
        return _fallback()

    if not picks:
        return _fallback()

    ai_quota.consume(request)
    return DiscoverResult(
        mode="ai",
        answer=intro or None,
        recipes=[DiscoveredRecipe(**p) for p in picks],
        remaining=ai_quota.remaining(request),
    )


@router.get("/categories", response_model=list[Category])
@limiter.limit(settings.rate_limit_read)
async def get_categories(request: Request, response: Response, pool: DbPool):
    return await list_categories(pool)


@router.get("/recipes", response_model=RecipeListResponse)
@limiter.limit(settings.rate_limit_read)
async def list_recipes_endpoint(
    request: Request,
    response: Response,
    pool: DbPool,
    limit: int = Query(20, ge=1, le=50, description="Max recipes per page"),
    cursor: str | None = Query(
        None, max_length=512, description="Opaque cursor from a previous page"
    ),
    category: int | None = Query(None, ge=1, description="Filter by category id"),
):
    cursor_created_at = None
    cursor_url = None
    if cursor is not None:
        try:
            cursor_created_at, cursor_url = decode_cursor(cursor)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid cursor")

    rows, has_more = await list_recipes(
        pool, limit, cursor_created_at, cursor_url, category
    )

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = encode_cursor(last["created_at"], last["url"])

    items = [
        RecipeCard(
            title=r["title"],
            source_url=r["url"],
            image_url=r["image_url"],
            prep_time=r["prep_time"],
            cook_time=r["cook_time"],
            total_time=r["total_time"],
            servings=r["servings"],
            category=r["category"],
        )
        for r in rows
    ]
    return RecipeListResponse(items=items, next_cursor=next_cursor)


@router.get("/similar", response_model=list[SimilarRecipe])
@limiter.limit(settings.rate_limit_read)
async def similar_recipes(
    request: Request,
    response: Response,
    pool: DbPool,
    url: str = Query(..., description="Source recipe URL"),
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
@limiter.limit(settings.rate_limit_expensive)
async def search(
    request: Request,
    response: Response,
    pool: DbPool,
    q: str = Query(..., min_length=1, max_length=500, description="Free-text recipe search query"),
    limit: int = Query(10, ge=1, le=50),
):
    try:
        query_embedding = await embed_query(q)
    except Exception:
        raise HTTPException(status_code=503, detail="Search is unavailable — the embedding service is not reachable")
    return await search_recipes(pool, query_embedding, limit)