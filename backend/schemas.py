from pydantic import BaseModel, HttpUrl

class ExtractRequest(BaseModel):
    url: HttpUrl
 
 
class Recipe(BaseModel):
    title: str
    source_url: str
    image_url: str | None = None
    prep_time: str | None = None
    cook_time: str | None = None
    total_time: str | None = None
    servings: str | None = None
    ingredients: list[str]
    instructions: list[str]
