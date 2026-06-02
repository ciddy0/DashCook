import logging

import ollama

from config import get_settings

logger = logging.getLogger(__name__)

SEARCH_TASK = "Given a recipe search query, retrieve recipes that match it"

def build_embed_text(recipe_data: dict) -> str:
    title = (recipe_data.get("title") or "").strip()

    seen: set[str] = set()
    names: list[str] = []
    for ing in recipe_data.get("ingredients", []):
        name = _ingredient_name(ing)
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    return f"{title} | {', '.join(names)}"

def _ingredient_name(ing) -> str:
    """Handle both Ingredient models (from parse_recipe) and plain dicts."""
    if isinstance(ing, dict):
        return (ing.get("name") or "").strip()
    return (getattr(ing, "name", "") or "").strip()

async def _embed(text: str) -> list[float]:
    """Single embedding call. Raises on failure."""
    settings = get_settings()
    client = ollama.AsyncClient(host=settings.ollama_host)
    response = await client.embed(model=settings.embedding_model, input=text)
    return response["embeddings"][0]

async def generate_embedding(recipe_data: dict) -> list[float] | None:
    text = build_embed_text(recipe_data)

    try:
        return await _embed(text)
    except Exception as e:
        logger.warning("embedding generation failed (storing as null): %s", e)
        return None
    
async def embed_query(text: str) -> list[float]:
    prompt = f"Instruct: {SEARCH_TASK}\nQuery:{text}"
    return await _embed(prompt)