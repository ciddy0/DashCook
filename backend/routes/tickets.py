import json
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response

from config import get_settings
from db.tickets import create_ticket, get_ticket, list_tickets, update_ticket
from dependencies import DbPool, require_admin
from middleware.rate_limiter import get_client_ip, limiter
from models.tickets import (
    TicketCategory,
    TicketCreate,
    TicketCreatedResponse,
    TicketDetail,
    TicketListResponse,
    TicketStatus,
    TicketUpdate,
)
from utils.security import hash_ip

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

_MAX_USER_AGENT_LEN = 512


def _to_detail(row) -> TicketDetail:
    """Map a tickets row onto the admin-facing model.

    `metadata` comes back from asyncpg as raw JSON text, so it is decoded here
    rather than in each endpoint.
    """
    return TicketDetail(
        id=row["id"],
        category=row["category"],
        status=row["status"],
        subject=row["subject"],
        description=row["description"],
        recipe_url=row["recipe_url"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        submitter_ip_hash=row["submitter_ip_hash"],
        user_agent=row["user_agent"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


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

    items = [_to_detail(r) for r in rows]
    return TicketListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketDetail,
    dependencies=[Depends(require_admin)],
)
@limiter.limit(settings.rate_limit_read)
async def get_ticket_detail(
    request: Request,
    response: Response,
    pool: DbPool,
    ticket_id: UUID = Path(description="Ticket id"),
):
    row = await get_ticket(pool, ticket_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _to_detail(row)


@router.patch(
    "/tickets/{ticket_id}",
    response_model=TicketDetail,
    dependencies=[Depends(require_admin)],
)
@limiter.limit(settings.rate_limit_read)
async def patch_ticket(
    request: Request,
    response: Response,
    body: TicketUpdate,
    pool: DbPool,
    ticket_id: UUID = Path(description="Ticket id"),
):
    """Update a ticket's triage fields. Admin only; see models.TicketUpdate for
    what is mutable."""
    row = await update_ticket(
        pool,
        ticket_id,
        status=body.status.value if body.status else None,
        category=body.category.value if body.category else None,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Server-generated, enum-constrained values only — same rule as the create
    # path: no user free text and no IP in the logs.
    logger.info(
        "ticket updated id=%s status=%s category=%s",
        row["id"],
        row["status"],
        row["category"],
    )
    return _to_detail(row)
