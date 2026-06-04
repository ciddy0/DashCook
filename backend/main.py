from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from db.pool import create_pool
from middleware.rate_limiter import check_rate_limit, get_client_ip
from routes import health, recipes


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


app = FastAPI(
    title="SousChat",
    description="extract clean recipes from bloated websites",
    version="1.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if (request.method == "POST" and request.url.path == "/url") or (
        request.method == "GET" and request.url.path == "/search"
    ):
        ip = get_client_ip(request)
        allowed, retry_after = check_rate_limit(ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)


app.include_router(health.router)
app.include_router(recipes.router)
