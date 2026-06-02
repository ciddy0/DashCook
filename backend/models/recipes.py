from pydantic import BaseModel


class Ingredient(BaseModel):
    raw: str
    name: str
    quantity: float | None
    quantity_max: float | None
    unit: str | None
    scalable: bool = True


class Recipe(BaseModel):
    title: str
    source_url: str
    image_url: str | None = None
    prep_time: str | None = None
    cook_time: str | None = None
    total_time: str | None = None
    servings: str | None = None
    ingredients: list[Ingredient]
    instructions: list[str]

class SimilarRecipe(BaseModel):
    title: str
    source_url: str
    image_url: str | None = None
    distance: float

