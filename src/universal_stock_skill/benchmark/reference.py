from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from universal_stock_skill.evidence.collection import EvidenceItem


class FinancialReferencePeriod(BaseModel):
    fiscal_year: str = Field(min_length=1)
    period_end: date
    values_million_yen: dict[str, Decimal]
    per_share_yen: dict[str, Decimal] = Field(default_factory=dict)
    ratios: dict[str, Decimal] = Field(default_factory=dict)
    share_counts: dict[str, int] = Field(default_factory=dict)


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

    @model_validator(mode="after")
    def validate_reference_case(self) -> StockReferenceCase:
        fiscal_years = [period.fiscal_year for period in self.periods]
        if len(fiscal_years) != len(set(fiscal_years)):
            raise ValueError("reference fiscal_year values must be unique")

        normalized_symbol = self.symbol.strip().upper()
        for item in self.qualitative_evidence:
            if item.symbol.strip().upper() != normalized_symbol:
                raise ValueError(
                    f"reference evidence symbol mismatch: {item.symbol}"
                )
            if item.record.published_at > self.as_of:
                raise ValueError(
                    f"reference evidence {item.record.source_id} is newer than as_of"
                )

        return self

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
