async def assign_category(pool, embedding) -> tuple[int, str] | None:
    """Return (id, name) of the nearest category centroid to `embedding`.

    Returns None if there are no categories yet or `embedding` is None. Uses pgvector
    cosine distance (<=>) in the original embedding space, so it's deterministic and
    stable across ingests (no re-clustering needed per recipe).
    """
    if embedding is None:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name FROM categories ORDER BY centroid <=> $1 LIMIT 1",
            embedding,
        )
    if row is None:
        return None
    return row["id"], row["name"]


async def list_categories(pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, description FROM categories ORDER BY name"
        )
    return [
        {"id": r["id"], "name": r["name"], "description": r["description"]}
        for r in rows
    ]
