from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SourceType = Literal[
    "filing",
    "timely_disclosure",
    "price",
    "news",
    "company_ir",
    "other",
]


class SourceRecord(BaseModel):
    source_id: str = Field(min_length=1)
    source_type: SourceType
    title: str = Field(min_length=1)
    published_at: datetime
    retrieved_at: datetime
    effective_at: datetime | None = None
    url: str | None = None
    content_hash: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("published_at", "retrieved_at", "effective_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("timestamps must be timezone-aware")
        return value
