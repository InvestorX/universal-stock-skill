from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class FinancialSnapshot(BaseModel):
    symbol: str = Field(min_length=1)
    as_of: datetime
    price: float
    revenue: float
    operating_income: float
    net_income: float
    eps: float
    bps: float
    average_equity: float
    operating_cash_flow: float
    capital_expenditure: float
    market_cap: float
    nopat: float | None = None
    average_invested_capital: float | None = None

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        return value


class StockMetrics(BaseModel):
    operating_margin: float
    per: float
    pbr: float
    roe: float
    free_cash_flow: float
    free_cash_flow_yield: float
    roic: float | None = None
