import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from db.pool import create_pool
from middleware.rate_limiter import limiter
from routes import health, recipes, tickets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    allow_headers=["Content-Type", "Accept", "X-Admin-Token"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    """Reject oversized request bodies early with 413.

    Checks the declared Content-Length; for requests without one (e.g. chunked)
    the downstream Pydantic field limits still bound what we accept.
    """
    content_length = request.headers.get("Content-Length")
    if content_length is not None:
        try:
            if int(content_length) > settings.max_request_body_bytes:
                return JSONResponse(
                    status_code=413, content={"detail": "Request body too large"}
                )
        except ValueError:
            return JSONResponse(
                status_code=400, content={"detail": "Invalid Content-Length"}
            )
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak internal error details or tracebacks to clients."""
    logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router)
app.include_router(recipes.router)
app.include_router(tickets.router)
