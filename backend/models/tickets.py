import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

# Cap the serialized size of the free-form metadata object so a caller can't
# smuggle a huge payload past the per-field length limits.
_MAX_METADATA_BYTES = 2048
_MAX_METADATA_KEYS = 30


class TicketCategory(str, Enum):
    parser = "parser"
    recipe = "recipe"
    account = "account"
    bug = "bug"
    feature_request = "feature_request"
    other = "other"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketCreate(BaseModel):
    # extra="forbid": reject unknown fields instead of silently dropping them.
    # str_strip_whitespace: trim surrounding whitespace on every string field.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: TicketCategory
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    recipe_url: HttpUrl | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def _cap_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > _MAX_METADATA_KEYS:
            raise ValueError(f"metadata may not exceed {_MAX_METADATA_KEYS} keys")
        try:
            serialized = json.dumps(value)
        except (TypeError, ValueError):
            raise ValueError("metadata must be JSON-serializable")
        if len(serialized.encode("utf-8")) > _MAX_METADATA_BYTES:
            raise ValueError(
                f"metadata may not exceed {_MAX_METADATA_BYTES} bytes when serialized"
            )
        return value


class TicketCreatedResponse(BaseModel):
    """Minimal acknowledgement. We deliberately do not echo stored content back."""

    id: UUID
    status: TicketStatus
    created_at: datetime


class TicketDetail(BaseModel):
    id: UUID
    category: TicketCategory
    status: TicketStatus
    subject: str
    description: str
    recipe_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    submitter_ip_hash: str | None = None
    user_agent: str | None = None
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    items: list[TicketDetail]
    total: int
    limit: int
    offset: int
