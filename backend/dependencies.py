import secrets
from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, Request

from config import get_settings


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


DbPool = Annotated[asyncpg.Pool, Depends(get_pool)]


def require_admin(request: Request) -> None:
    """Gate owner-only endpoints behind a shared secret admin token.

    Fails closed: if no token is configured the endpoint is unavailable (503)
    rather than open. The supplied token is compared in constant time and is
    never echoed back or logged.
    """
    settings = get_settings()
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="Admin endpoint not configured")
    supplied = request.headers.get("X-Admin-Token", "")
    if not secrets.compare_digest(supplied, settings.admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
