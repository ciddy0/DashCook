import json
from uuid import UUID

import asyncpg


async def create_ticket(
    pool: asyncpg.Pool,
    *,
    id: UUID,
    category: str,
    subject: str,
    description: str,
    recipe_url: str | None,
    metadata: dict,
    ip_hash: str | None,
    user_agent: str | None,
) -> asyncpg.Record:
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO tickets (
                id, category, subject, description, recipe_url,
                metadata, submitter_ip_hash, user_agent
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, status, created_at
            """,
            id,
            category,
            subject,
            description,
            recipe_url,
            json.dumps(metadata),
            ip_hash,
            user_agent,
        )


# Every column the admin ticket views render. Kept in one place so the list,
# fetch and update queries can never drift apart.
_DETAIL_COLUMNS = """
    id, category, status, subject, description, recipe_url,
    metadata, submitter_ip_hash, user_agent, created_at, updated_at
"""


async def get_ticket(pool: asyncpg.Pool, ticket_id: UUID) -> asyncpg.Record | None:
    """Fetch one ticket, or None when no row has that id."""
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            f"SELECT {_DETAIL_COLUMNS} FROM tickets WHERE id = $1", ticket_id
        )


async def update_ticket(
    pool: asyncpg.Pool,
    ticket_id: UUID,
    *,
    status: str | None = None,
    category: str | None = None,
) -> asyncpg.Record | None:
    """Patch the admin-curated fields of a ticket. Returns None if it's gone.

    A NULL argument leaves its column untouched (COALESCE), so this is a true
    partial update. The casts are required: without them asyncpg can't infer a
    type for a NULL parameter inside COALESCE.
    """
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            f"""
            UPDATE tickets
               SET status     = COALESCE($2::text, status),
                   category   = COALESCE($3::text, category),
                   updated_at = NOW()
             WHERE id = $1
            RETURNING {_DETAIL_COLUMNS}
            """,
            ticket_id,
            status,
            category,
        )


async def list_tickets(
    pool: asyncpg.Pool,
    *,
    limit: int = 20,
    offset: int = 0,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[asyncpg.Record], int]:
    """Offset-paginated ticket list, newest first, with optional filters.

    Returns (rows, total). `total` is the count matching the same filters,
    ignoring limit/offset, so the caller can render pagination controls.

    All user values are bound as parameters; `search` is used inside a bound
    ILIKE argument, so `%`/`_` are matched literally within the value and there
    is no injection surface.
    """
    # $1 category filter, $2 status filter, $3 search term (all NULL = no filter).
    filter_params: list = [category, status, search]
    where = """
        WHERE ($1::text IS NULL OR category = $1)
          AND ($2::text IS NULL OR status = $2)
          AND ($3::text IS NULL
               OR subject ILIKE '%' || $3 || '%'
               OR description ILIKE '%' || $3 || '%')
    """

    async with pool.acquire() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM tickets {where}", *filter_params
        )
        rows = await conn.fetch(
            f"""
            SELECT {_DETAIL_COLUMNS}
            FROM tickets
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ${len(filter_params) + 1} OFFSET ${len(filter_params) + 2}
            """,
            *filter_params,
            limit,
            offset,
        )

    return rows, total
