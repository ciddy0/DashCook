async def assign_category(pool, embedding) -> tuple[int, str] | None:
    """Return (id, name) of the best category for `embedding`.

    Picks the nearest real (non-catchall) centroid, but only if `embedding` is within that
    category's `radius`; otherwise falls back to the 'Other' catch-all. Uses pgvector cosine
    distance (<=>) in the original embedding space, so it's deterministic and stable across
    ingests (no re-clustering needed per recipe). Returns None if there are no categories
    yet or `embedding` is None.
    """
    if embedding is None:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name FROM categories
            WHERE NOT is_catchall
              AND (radius IS NULL OR (centroid <=> $1) <= radius)
            ORDER BY centroid <=> $1
            LIMIT 1
            """,
            embedding,
        )
        if row is None:
            row = await conn.fetchrow(
                "SELECT id, name FROM categories WHERE is_catchall LIMIT 1"
            )
    if row is None:
        return None
    return row["id"], row["name"]


async def list_categories(pool) -> list[dict]:
    async with pool.acquire() as conn:
        # Catch-all ("Other") sorts last; real categories alphabetically.
        rows = await conn.fetch(
            "SELECT id, name, description FROM categories ORDER BY is_catchall, name"
        )
    return [
        {"id": r["id"], "name": r["name"], "description": r["description"]}
        for r in rows
    ]
