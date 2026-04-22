import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.pool import create_pool
from database.cache import get_cached_recipe, cache_recipe
from helpers import normalize_url
from rate_limiter import check_rate_limit, get_client_ip
from scraper import fetch_page
from parser import parse_recipe
from schemas import ExtractRequest, Recipe
from validators import validate_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


app = FastAPI(
    title="DashCook",
    description="extract clean recipes from bloated websites",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins.split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/url":
        ip = get_client_ip(request)
        allowed, retry_after = check_rate_limit(ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)

@app.get("/")
def home():
    return 'hai!'

@app.get("/ping")
def ping():
    return 'pong'

@app.post("/url", response_model=Recipe)
async def get_recipe(req: Request, body: ExtractRequest):
    url = normalize_url(str(body.url))

    try:
        validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    pool = req.app.state.pool
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

    await cache_recipe(pool, url, recipe_data)
    
    return Recipe(source_url=url, **recipe_data)
