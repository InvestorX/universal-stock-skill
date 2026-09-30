from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BenchmarkCase(BaseModel):
    case_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    as_of: datetime
    task: str = Field(min_length=1)
    allowed_sources: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        return value

    def allows_publication(self, published_at: datetime) -> bool:
        if published_at.tzinfo is None or published_at.utcoffset() is None:
            raise ValueError("published_at must be timezone-aware")
        return published_at <= self.as_of
