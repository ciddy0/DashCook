import asyncio
import logging

from config import get_settings
from db.recipes import get_recipes_by_urls

logger = logging.getLogger(__name__)


async def rerank_results(
    query: str, results: list[dict], pool, top_n: int = 10
) -> list[dict]:
    settings = get_settings()
    if not settings.cohere_api_key:
        return results[:top_n]

    try:
        import cohere

        co = cohere.Client(api_key=settings.cohere_api_key)

        urls = [r["source_url"] for r in results]
        recipes_by_url = await get_recipes_by_urls(pool, urls)

        documents = []
        for r in results:
            recipe = recipes_by_url.get(r["source_url"], {})
            documents.append(recipe.get("title", r.get("title", "")))

        response = await asyncio.to_thread(
            co.rerank,
            model="rerank-english-v3.0",
            query=query,
            documents=documents,
            top_n=top_n,
        )

        reranked = []
        for item in response.results:
            result = results[item.index].copy()
            result["score"] = item.relevance_score
            reranked.append(result)
        return reranked

    except Exception:
        logger.warning("Cohere reranking failed, falling back to RRF order", exc_info=True)
        return results[:top_n]
