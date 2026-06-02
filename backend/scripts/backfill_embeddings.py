"""
Backfill NULL embeddings for recipes already in the database.

Queries rows where embedding IS NULL, builds embed text via
build_embed_text(), sends batches to Ollama's embed endpoint,
and updates each row.

Usage:
    python scripts/backfill_embeddings.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Allow imports from the backend root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ollama

from config import get_settings
from db.pool import create_pool
from services.embedder import build_embed_text

BATCH_SIZE = 5


async def backfill() -> None:
    settings = get_settings()
    pool = await create_pool()

    try:
        rows = await pool.fetch(
            "SELECT url, title, ingredients FROM recipes WHERE embedding IS NULL"
        )

        if not rows:
            print("No recipes need embedding.")
            return

        total = len(rows)
        print(f"Found {total} recipes without embeddings")

        # Build embed texts for each row
        items = []
        for row in rows:
            recipe_data = {
                "title": row["title"],
                "ingredients": json.loads(row["ingredients"]),
            }
            items.append({
                "url": row["url"],
                "text": build_embed_text(recipe_data),
            })

        # Process in batches
        client = ollama.AsyncClient(host=settings.ollama_host)
        batches = [items[i : i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
        backfilled = 0

        for batch_num, batch in enumerate(batches, 1):
            texts = [item["text"] for item in batch]
            response = await client.embed(
                model=settings.embedding_model, input=texts
            )
            embeddings = response["embeddings"]

            for item, embedding in zip(batch, embeddings):
                await pool.execute(
                    "UPDATE recipes SET embedding = $1 WHERE url = $2",
                    embedding,
                    item["url"],
                )

            backfilled += len(batch)
            print(f"Batch {batch_num}/{len(batches)} done ({backfilled}/{total} rows)")

        print(f"\nBackfilled {backfilled} recipes.")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(backfill())
