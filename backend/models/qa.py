from pydantic import BaseModel, ConfigDict, Field, field_validator

_MAX_LINE_LEN = 400


class QATurn(BaseModel):
    """One completed exchange from earlier in the same conversation, so the
    assistant can resolve follow-ups like "what about margarine?"."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1, max_length=2000)


class RecipeQuestion(BaseModel):
    """A question about a specific recipe, sent from the recipe page.

    The recipe context is supplied by the client (it already holds the parsed
    recipe locally) rather than looked up server-side, so the helper works for
    freshly extracted recipes that aren't in the database yet.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=1, max_length=300)
    servings: str | None = Field(default=None, max_length=60)
    total_time: str | None = Field(default=None, max_length=60)
    ingredients: list[str] = Field(min_length=1, max_length=120)
    instructions: list[str] = Field(default_factory=list, max_length=80)
    # Prior Q&A in this conversation (oldest first). Capped so the follow-up
    # context can't grow unbounded.
    history: list[QATurn] = Field(default_factory=list, max_length=8)

    @field_validator("ingredients", "instructions")
    @classmethod
    def _cap_lines(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for line in value:
            line = line.strip()
            if line:
                cleaned.append(line[:_MAX_LINE_LEN])
        return cleaned


class RecipeAnswer(BaseModel):
    answer: str
