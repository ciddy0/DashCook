import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request, Response

from config import get_settings
from db.tickets import create_ticket, list_tickets
from dependencies import DbPool, require_admin
from middleware.rate_limiter import get_client_ip, limiter
from models.tickets import (
    TicketCategory,
    TicketCreate,
    TicketCreatedResponse,
    TicketDetail,
    TicketListResponse,
    TicketStatus,
)
from utils.security import hash_ip

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

_MAX_USER_AGENT_LEN = 512


@router.post("/tickets", response_model=TicketCreatedResponse, status_code=201)
@limiter.limit(settings.rate_limit_ticket)
async def submit_ticket(
    request: Request,
    response: Response,
    body: TicketCreate,
    pool: DbPool,
):
    ticket_id = uuid4()
    user_agent = request.headers.get("User-Agent")
    if user_agent is not None:
        user_agent = user_agent[:_MAX_USER_AGENT_LEN]

    row = await create_ticket(
        pool,
        id=ticket_id,
        category=body.category.value,
        subject=body.subject,
        description=body.description,
        recipe_url=str(body.recipe_url) if body.recipe_url else None,
        metadata=body.metadata,
        ip_hash=hash_ip(get_client_ip(request), settings.ip_hash_salt),
        user_agent=user_agent,
    )

    # Log only server-generated, structured values — never user free text or IP
    # — so there is no log-injection or PII-leakage surface.
    logger.info("ticket created id=%s category=%s", row["id"], body.category.value)

    return TicketCreatedResponse(
        id=row["id"], status=row["status"], created_at=row["created_at"]
    )


@router.get(
    "/tickets",
    response_model=TicketListResponse,
    dependencies=[Depends(require_admin)],
)
@limiter.limit(settings.rate_limit_read)
async def get_tickets(
    request: Request,
    response: Response,
    pool: DbPool,
    limit: int = Query(20, ge=1, le=100, description="Max tickets per page"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    category: TicketCategory | None = Query(None, description="Filter by category"),
    status: TicketStatus | None = Query(None, description="Filter by status"),
    search: str | None = Query(
        None, min_length=1, max_length=100, description="Match subject/description"
    ),
):
    rows, total = await list_tickets(
        pool,
        limit=limit,
        offset=offset,
        category=category.value if category else None,
        status=status.value if status else None,
        search=search,
    )

    items = [
        TicketDetail(
            id=r["id"],
            category=r["category"],
            status=r["status"],
            subject=r["subject"],
            description=r["description"],
            recipe_url=r["recipe_url"],
            metadata=json.loads(r["metadata"]) if r["metadata"] else {},
            submitter_ip_hash=r["submitter_ip_hash"],
            user_agent=r["user_agent"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]
    return TicketListResponse(items=items, total=total, limit=limit, offset=offset)
