"""
Build the recipe category taxonomy.
=====================================
Occasionally-run script (NOT per-request). It:

1. Fetches all recipe embeddings from the database.
2. Clusters them (UMAP -> K-Means, best K by silhouette).
3. Computes each cluster's centroid in the ORIGINAL 3072-d embedding space.
4. Names each cluster with an LLM from its most representative recipe titles.
5. Rebuilds the `categories` table and reassigns every recipe to its nearest centroid.

New recipes added between runs are categorised automatically at ingest time
(see db/categories.py::assign_category), so this only needs to run when you want to
refresh the taxonomy (e.g. weekly/monthly or when new kinds of recipes appear).

Usage:
    cd backend/
    python scripts/build_categories.py
"""

import asyncio
import json
import os
import sys

import asyncpg
import numpy as np
from openai import AsyncOpenAI
from pgvector.asyncpg import register_vector
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from umap import UMAP

# Allow importing config.py from the backend root.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
from config import get_settings  # noqa: E402

K_RANGE = range(3, 16)  # 3-15 inclusive
EXEMPLARS_PER_CLUSTER = 20  # titles shown to the LLM when naming a cluster


async def _connect() -> asyncpg.Connection:
    settings = get_settings()
    dsn = settings.supabase_url or settings.database_url
    ssl = "require" if settings.supabase_url else None
    conn = await asyncpg.connect(dsn=dsn, ssl=ssl)
    await register_vector(conn)
    return conn


async def fetch_recipes(conn) -> list[dict]:
    rows = await conn.fetch(
        "SELECT url, title, embedding FROM recipes WHERE embedding IS NOT NULL"
    )
    return [
        {"url": r["url"], "title": r["title"], "embedding": np.array(r["embedding"])}
        for r in rows
    ]


def cluster(embeddings: np.ndarray) -> np.ndarray:
    """Return a cluster label per row. UMAP->50 for quality, K-Means for centroids."""
    print("  UMAP 3072 -> 50 ...")
    reduced = UMAP(
        n_components=50, random_state=42, n_neighbors=15, metric="cosine"
    ).fit_transform(embeddings)

    best_score, best_labels, best_k = -1.0, None, 0
    for k in K_RANGE:
        if k >= len(embeddings):
            break
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(reduced)
        score = silhouette_score(reduced, labels)
        if score > best_score:
            best_score, best_labels, best_k = score, labels, k
    print(f"  Best K={best_k} (silhouette={best_score:.4f})")
    return best_labels


def exemplar_titles(recipes: list[dict], members: np.ndarray, centroid: np.ndarray) -> list[str]:
    """Titles of the members closest to the centroid (most representative)."""
    idxs = np.where(members)[0]
    dists = [np.linalg.norm(recipes[i]["embedding"] - centroid) for i in idxs]
    order = np.argsort(dists)
    return [recipes[idxs[j]]["title"] for j in order[:EXEMPLARS_PER_CLUSTER]]


async def name_cluster(client: AsyncOpenAI, model: str, titles: list[str]) -> dict:
    prompt = (
        "You are naming a category for a recipe browsing app. Given these recipe "
        "titles from one cluster, respond with a JSON object "
        '{"name": "...", "description": "..."} where name is a short (1-3 word) '
        "human-friendly category label and description is one short sentence. "
        "Titles:\n- " + "\n- ".join(titles)
    )
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    data = json.loads(resp.choices[0].message.content)
    return {"name": data["name"].strip(), "description": (data.get("description") or "").strip()}


async def rebuild(conn, categories: list[dict]):
    """Replace the categories table and reassign every embedded recipe. Transactional."""
    async with conn.transaction():
        await conn.execute("TRUNCATE categories RESTART IDENTITY")
        for cat in categories:
            await conn.execute(
                "INSERT INTO categories (name, description, centroid) VALUES ($1, $2, $3)",
                cat["name"],
                cat["description"],
                cat["centroid"],
            )
        # Reassign all recipes to the nearest new centroid.
        await conn.execute(
            """
            UPDATE recipes r
            SET section_id = (
                SELECT c.id FROM categories c
                ORDER BY c.centroid <=> r.embedding
                LIMIT 1
            )
            WHERE r.embedding IS NOT NULL
            """
        )


async def main():
    settings = get_settings()
    conn = await _connect()
    try:
        print("1/4  Fetching recipe embeddings ...")
        recipes = await fetch_recipes(conn)
        if len(recipes) < 10:
            print(f"Only {len(recipes)} embedded recipes - need at least 10. Aborting.")
            return
        print(f"     Loaded {len(recipes)} recipes.")

        embeddings = np.stack([r["embedding"] for r in recipes])

        print("2/4  Clustering ...")
        labels = cluster(embeddings)

        print("3/4  Naming clusters with the LLM ...")
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        categories = []
        for cl in sorted(set(labels)):
            members = labels == cl
            centroid = embeddings[members].mean(axis=0)  # 3072-d, original space
            titles = exemplar_titles(recipes, members, centroid)
            named = await name_cluster(client, settings.category_model, titles)
            print(f"    Cluster {cl}: {named['name']} ({int(members.sum())} recipes)")
            categories.append({**named, "centroid": centroid.tolist()})

        print("4/4  Writing categories and reassigning recipes ...")
        await rebuild(conn, categories)
        print(f"\nDone! {len(categories)} categories created and all recipes reassigned.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
