import json
import re
from bs4 import BeautifulSoup

def parse_recipe(html: str) -> dict:
    """
    basically extract the recipe object from json-ld markup in the html
    """
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    recipe_data = None

    for script in scripts:
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue
        
        recipe_data = _find_recipe(data)
        if recipe_data:
            break
    if not recipe_data:
        raise ValueError("no recipe schema found on this page D:")
    
    return _extract_fields(recipe_data)

def _is_recipe(item: dict) -> bool:
    """Check if an item's @type is Recipe (handles string or list)."""
    schema_type = item.get("@type")
    if isinstance(schema_type, str):
        return schema_type == "Recipe"
    if isinstance(schema_type, list):
        return "Recipe" in schema_type
    return False


def _find_recipe(data) -> dict | None:
    if isinstance(data, dict):
        if _is_recipe(data):
            return data
        if "@graph" in data:
            for item in data["@graph"]:
                if isinstance(item, dict) and _is_recipe(item):
                    return item
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and _is_recipe(item):
                return item
    return None

def _extract_fields(recipe: dict) -> dict:
    """
    pull out and normalize the fields we care about
    """
    return {
        "title": _clean_text(recipe.get("name", "Untitled Recipe")),
        "image_url": _extract_image(recipe.get("image")),
        "prep_time": _parse_duration(recipe.get("prepTime")),
        "cook_time": _parse_duration(recipe.get("cookTime")),
        "total_time": _parse_duration(recipe.get("totalTime")),
        "servings": _extract_servings(recipe.get("recipeYield")),
        "ingredients": _extract_ingredients(recipe.get("recipeIngredient", [])),
        "instructions": _extract_instructions(recipe.get("recipeInstructions", [])),
    }
 
 
def _extract_image(image) -> str | None:
    """
    handle image as string, list of strings, or ImageObject
    """
    if isinstance(image, str):
        return image
    if isinstance(image, list) and len(image) > 0:
        first = image[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("url")
    if isinstance(image, dict):
        return image.get("url")
    return None

def _extract_servings(recipe_yield) -> str | None:
    """
    normalize recipeYield to a single string
    """
    if isinstance(recipe_yield, str):
        return recipe_yield
    if isinstance(recipe_yield, list) and len(recipe_yield) > 0:
        return str(recipe_yield[0])
    return None
 
 
def _extract_ingredients(ingredients: list) -> list[str]:
    """
    clean up ingredient strings
    """
    return [_clean_text(ing) for ing in ingredients if isinstance(ing, str)]
 
 
def _extract_instructions(instructions) -> list[str]:
    """
    handle both plain strings and HowToStep objects
    """
    steps = []
 
    if isinstance(instructions, list):
        for step in instructions:
            if isinstance(step, str):
                steps.append(_clean_text(step))
            elif isinstance(step, dict):
                if step.get("@type") == "HowToSection":
                    for sub in step.get("itemListElement", []):
                        if isinstance(sub, dict) and sub.get("text"):
                            steps.append(_clean_text(sub["text"]))
                else:
                    text = step.get("text", "")
                    if text:
                        steps.append(_clean_text(text))
 
    return steps
 
 
def _parse_duration(duration: str | None) -> str | None:
    """
    convert ISO 8601 duration (e.g. PT1H30M) to a readable string
    """
    if not duration:
        return None
 
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", duration)
    if not match:
        return None
 
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
 
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
 
    return " ".join(parts) if parts else None
 
 
def _clean_text(text: str) -> str:
    """
    strip HTML tags and decode entities
    """
    cleaned = BeautifulSoup(text, "html.parser").get_text()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned