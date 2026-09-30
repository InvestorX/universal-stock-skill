from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field, field_validator, model_validator


class MarketSnapshot(BaseModel):
    symbol: str = Field(min_length=1)
    observed_at: datetime
    price: float = Field(gt=0)
    currency: str = Field(min_length=3)
    source: str = Field(min_length=1)
    market_cap: float | None = Field(default=None, gt=0)
    shares_outstanding: float | None = Field(default=None, gt=0)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def derive_market_cap(self) -> MarketSnapshot:
        if self.market_cap is None and self.shares_outstanding is not None:
            self.market_cap = self.price * self.shares_outstanding
        return self

    @property
    def has_market_cap(self) -> bool:
        return self.market_cap is not None


class MarketDataSource(Protocol):
    async def get_market_snapshot(
        self,
        symbol: str,
        as_of: datetime,
    ) -> MarketSnapshot:
        ...
