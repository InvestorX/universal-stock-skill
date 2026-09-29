from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from universal_stock_skill.evidence.collection import EvidenceItem


class FinancialReferencePeriod(BaseModel):
    fiscal_year: str = Field(min_length=1)
    period_end: date
    values_million_yen: dict[str, Decimal]
    per_share_yen: dict[str, Decimal] = Field(default_factory=dict)
    ratios: dict[str, Decimal] = Field(default_factory=dict)


class StockReferenceCase(BaseModel):
    case_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    accounting_standard: str = Field(min_length=1)
    as_of: datetime
    periods: list[FinancialReferencePeriod]
    qualitative_evidence: list[EvidenceItem] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        return value

    def period(self, fiscal_year: str) -> FinancialReferencePeriod:
        for period in self.periods:
            if period.fiscal_year == fiscal_year:
                return period
        raise KeyError(f"reference period not found: {fiscal_year}")


def pct_change(current: Decimal, prior: Decimal) -> Decimal:
    if prior == 0:
        raise ValueError("prior value must not be zero")
    return current / prior - Decimal(1)


def ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        raise ValueError("denominator must not be zero")
    return numerator / denominator
