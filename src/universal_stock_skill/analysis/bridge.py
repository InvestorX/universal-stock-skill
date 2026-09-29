from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from universal_stock_skill.analysis.models import FinancialSnapshot
from universal_stock_skill.data.canonical import (
    CanonicalFinancialSet,
    CanonicalMetric,
    MappingMatchType,
)


SNAPSHOT_CANONICAL_REQUIREMENTS = (
    CanonicalMetric.REVENUE,
    CanonicalMetric.OPERATING_INCOME,
    CanonicalMetric.NET_INCOME,
    CanonicalMetric.EPS,
    CanonicalMetric.BPS,
    CanonicalMetric.CF_OPERATING,
)


class MissingCanonicalMetric(ValueError):
    pass


class SnapshotCanonicalReadiness(BaseModel):
    ready: bool
    required_metrics: list[CanonicalMetric]
    missing_metrics: list[CanonicalMetric]
    fallback_metrics: list[CanonicalMetric]


class SnapshotBridgeInputs(BaseModel):
    symbol: str = Field(min_length=1)
    as_of: datetime
    price: float
    market_cap: float
    average_equity: float
    capital_expenditure: float
    nopat: float | None = None
    average_invested_capital: float | None = None

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        return value


def evaluate_snapshot_readiness(
    canonical: CanonicalFinancialSet,
) -> SnapshotCanonicalReadiness:
    missing = [
        metric
        for metric in SNAPSHOT_CANONICAL_REQUIREMENTS
        if canonical.get(metric) is None
    ]
    fallback = [
        metric
        for metric in SNAPSHOT_CANONICAL_REQUIREMENTS
        if (
            (fact := canonical.get(metric)) is not None
            and fact.match_type == MappingMatchType.EXTENSION_FALLBACK
        )
    ]

    return SnapshotCanonicalReadiness(
        ready=not missing,
        required_metrics=list(SNAPSHOT_CANONICAL_REQUIREMENTS),
        missing_metrics=missing,
        fallback_metrics=fallback,
    )


def build_financial_snapshot(
    canonical: CanonicalFinancialSet,
    inputs: SnapshotBridgeInputs,
) -> FinancialSnapshot:
    return FinancialSnapshot(
        symbol=inputs.symbol,
        as_of=inputs.as_of,
        price=inputs.price,
        revenue=_require(canonical, CanonicalMetric.REVENUE),
        operating_income=_require(canonical, CanonicalMetric.OPERATING_INCOME),
        net_income=_require(canonical, CanonicalMetric.NET_INCOME),
        eps=_require(canonical, CanonicalMetric.EPS),
        bps=_require(canonical, CanonicalMetric.BPS),
        average_equity=inputs.average_equity,
        operating_cash_flow=_require(canonical, CanonicalMetric.CF_OPERATING),
        capital_expenditure=inputs.capital_expenditure,
        market_cap=inputs.market_cap,
        nopat=inputs.nopat,
        average_invested_capital=inputs.average_invested_capital,
    )


def _require(
    canonical: CanonicalFinancialSet,
    metric: CanonicalMetric,
) -> float:
    fact = canonical.get(metric)
    if fact is None:
        raise MissingCanonicalMetric(
            f"canonical metric is required for FinancialSnapshot: {metric.value}"
        )
    return float(fact.value)
