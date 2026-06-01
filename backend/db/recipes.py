import json

from pydantic import BaseModel


class _PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

async def get_cached_recipe(pool, url: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM recipes WHERE url = $1", url)
        if not row:
            return None
        return {
            "title": row["title"],
            "source_url": row["url"],
            "image_url": row["image_url"],
            "prep_time": row["prep_time"],
            "cook_time": row["cook_time"],
            "total_time": row["total_time"],
            "servings": row["servings"],
            "ingredients": json.loads(row["ingredients"]),
            "instructions": json.loads(row["instructions"]),
        }

async def cache_recipe(
    pool, url: str, recipe_data: dict, embedding: list[float] | None = None
):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO recipes (url, title, image_url, prep_time, cook_time, total_time, servings, ingredients, instructions, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (url) DO UPDATE SET
                title        = EXCLUDED.title,
                image_url    = EXCLUDED.image_url,
                prep_time    = EXCLUDED.prep_time,
                cook_time    = EXCLUDED.cook_time,
                total_time   = EXCLUDED.total_time,
                servings     = EXCLUDED.servings,
                ingredients  = EXCLUDED.ingredients,
                instructions = EXCLUDED.instructions,
                embedding    = COALESCE(EXCLUDED.embedding, recipes.embedding)
            """,
            url,
            recipe_data["title"],
            recipe_data.get("image_url"),
            recipe_data.get("prep_time"),
            recipe_data.get("cook_time"),
            recipe_data.get("total_time"),
            recipe_data.get("servings"),
            json.dumps(recipe_data["ingredients"], cls=_PydanticEncoder),
            json.dumps(recipe_data["instructions"]),
            embedding,
        )