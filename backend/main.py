from fastapi import FastAPI, HTTPException
from scraper import fetch_page
from parser import parse_recipe
from schemas import ExtractRequest, Recipe

app = FastAPI(
    title="DashCook",
    description="extract clean recipes from bloated websites",
    version="1.0.0"
)

@app.get("/")
def home():
    return 'hai!'

@app.get("/ping")
def ping():
    return 'pong'

@app.post("/url", response_model=Recipe)
async def get_recipe(request: ExtractRequest):
    # first lets get the page
    try:
        html = await fetch_page(str(request.url))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"failed to fetch URL D: {e}")
    
    # parse the recipe
    try: 
        recipe_data = parse_recipe(html)
    except ValueError as e:
        raise HTTPException(status_code = 422, detail=str(e))

    recipe = Recipe(source_url=str(request.url), **recipe_data)
    return recipe