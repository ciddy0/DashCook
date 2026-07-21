from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DiscoverRequest(BaseModel):
    """A free-text "what am I in the mood for" query from the chat widget."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=5, ge=1, le=8, description="Max recipes to return")


class DiscoveredRecipe(BaseModel):
    title: str
    source_url: str
    image_url: str | None = None
    total_time: str | None = None
    why: str | None = None


class DiscoverResult(BaseModel):
    """`mode` tells the client which path produced this.

    "ai"     — Claude picked and described the recipes.
    "search" — plain semantic search, because the daily budget ran out or the
               assistant was unreachable. Same shape, no prose.
    """

    mode: Literal["ai", "search"]
    answer: str | None = None
    recipes: list[DiscoveredRecipe]
    remaining: int = Field(description="AI requests left today for this client")
