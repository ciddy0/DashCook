import logging

import ollama

from config import get_settings

logger = logging.getLogger(__name__)

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

async def generate_embedding(recipe_data: dict) -> list[float] | None:
    settings = get_settings()
    text = build_embed_text(recipe_data)

    try:
        client = ollama.AsyncClient(host=settings.ollama_host)
        response = await client.embed(model=settings.embedding_model, input=text)
        return response["embeddings"][0]
    except Exception as e:
        logger.warning("embedding generation failed (storing as null): %s", e)
        return None
    
    