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
SAMPLE_PER_CLUSTER = 40  # titles shown to the LLM when naming a cluster
MEMBERSHIP_PERCENTILE = 90  # a recipe belongs if within this pctile of member distances


def _cosine_dists(vecs: np.ndarray, centroid: np.ndarray) -> np.ndarray:
    """Cosine distance (1 - cosine similarity) of each row to `centroid`.

    Matches pgvector's `<=>` operator so naming, radius and assignment all agree.
    """
    vn = np.linalg.norm(vecs, axis=1)
    cn = np.linalg.norm(centroid)
    denom = np.where(vn == 0, 1.0, vn) * (cn if cn != 0 else 1.0)
    return 1.0 - (vecs @ centroid) / denom


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


def sample_titles(recipes: list[dict], member_vecs: np.ndarray, member_idxs: np.ndarray,
                  centroid: np.ndarray) -> list[str]:
    """A representative spread of titles from near, median and far members.

    Sorting by distance to the centroid and picking evenly across the whole range (not
    just the closest) gives the LLM the cluster's full spread, so it names a broad
    umbrella instead of only the dense core.
    """
    order = np.argsort(_cosine_dists(member_vecs, centroid))
    n = min(SAMPLE_PER_CLUSTER, len(order))
    picks = np.linspace(0, len(order) - 1, n).round().astype(int)
    return [recipes[member_idxs[order[p]]]["title"] for p in picks]


async def name_cluster(client: AsyncOpenAI, model: str, titles: list[str]) -> dict:
    prompt = (
        "You are naming a category for a recipe browsing app. The titles below are a "
        "representative sample of one cluster, ranging from its most typical recipes to "
        "its edge cases. Respond with a JSON object "
        '{"name": "...", "description": "..."} where name is a short, BROAD umbrella '
        "label (up to ~4 words) wide enough to cover every title including the edge "
        "cases, and description is one short sentence. Prefer a general label (e.g. "
        '"Sweets & Treats") over a narrow one (e.g. "Comfort Desserts"). '
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
                "INSERT INTO categories (name, description, centroid, radius) "
                "VALUES ($1, $2, $3, $4)",
                cat["name"],
                cat["description"],
                cat["centroid"],
                cat["radius"],
            )
        # Catch-all for recipes outside every cluster's radius.
        await conn.execute(
            "INSERT INTO categories (name, description, centroid, radius, is_catchall) "
            "VALUES ('Other', 'Recipes that don''t fit another category.', NULL, NULL, TRUE)"
        )
        # Reassign every recipe to its nearest in-radius centroid, else the catch-all.
        await conn.execute(
            """
            UPDATE recipes r
            SET section_id = COALESCE(
                (SELECT c.id FROM categories c
                 WHERE NOT c.is_catchall
                   AND (c.radius IS NULL OR (c.centroid <=> r.embedding) <= c.radius)
                 ORDER BY c.centroid <=> r.embedding
                 LIMIT 1),
                (SELECT id FROM categories WHERE is_catchall LIMIT 1)
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
            member_idxs = np.where(members)[0]
            member_vecs = embeddings[members]
            centroid = member_vecs.mean(axis=0)  # 3072-d, original space
            dists = _cosine_dists(member_vecs, centroid)
            radius = float(np.percentile(dists, MEMBERSHIP_PERCENTILE))
            titles = sample_titles(recipes, member_vecs, member_idxs, centroid)
            named = await name_cluster(client, settings.category_model, titles)
            print(f"    Cluster {cl}: {named['name']} "
                  f"({int(members.sum())} recipes, radius={radius:.3f})")
            categories.append({**named, "centroid": centroid.tolist(), "radius": radius})

        print("4/4  Writing categories and reassigning recipes ...")
        await rebuild(conn, categories)
        print(f"\nDone! {len(categories)} categories created and all recipes reassigned.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
