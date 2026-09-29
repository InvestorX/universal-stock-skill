from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from universal_stock_skill.data.canonical import (
    CanonicalFinancialSeries,
    CanonicalMetric,
)
from universal_stock_skill.finance import cagr


class CanonicalMetricTrend(BaseModel):
    metric: CanonicalMetric
    current_value: Decimal
    prior_value: Decimal | None = None
    year_over_year: float | None = None
    cagr_value: float | None = None
    cagr_years: int | None = None


class CanonicalTrendSet(BaseModel):
    trends: list[CanonicalMetricTrend]
    missing: list[CanonicalMetric]

    def get(self, metric: CanonicalMetric) -> CanonicalMetricTrend | None:
        return next((item for item in self.trends if item.metric == metric), None)


def calculate_canonical_trends(
    series: CanonicalFinancialSeries,
    metrics: list[CanonicalMetric],
) -> CanonicalTrendSet:
    trends: list[CanonicalMetricTrend] = []
    missing: list[CanonicalMetric] = []

    for metric in metrics:
        trend = calculate_canonical_trend(series, metric)
        if trend is None:
            missing.append(metric)
        else:
            trends.append(trend)

    return CanonicalTrendSet(trends=trends, missing=missing)


def calculate_canonical_trend(
    series: CanonicalFinancialSeries,
    metric: CanonicalMetric,
) -> CanonicalMetricTrend | None:
    current = _value(series, metric, year_offset=0)
    if current is None:
        return None

    prior = _value(series, metric, year_offset=1)
    yoy = _growth_rate(current, prior) if prior is not None else None

    available_offsets = sorted(
        period.year_offset
        for period in series.periods
        if period.year_offset > 0
        and period.financials.get(metric) is not None
    )

    cagr_value: float | None = None
    cagr_years: int | None = None
    if available_offsets:
        oldest_offset = available_offsets[-1]
        oldest = _value(series, metric, year_offset=oldest_offset)
        if oldest is not None and oldest > 0 and current >= 0:
            cagr_value = cagr(
                float(oldest),
                float(current),
                float(oldest_offset),
            )
            cagr_years = oldest_offset

    return CanonicalMetricTrend(
        metric=metric,
        current_value=current,
        prior_value=prior,
        year_over_year=yoy,
        cagr_value=cagr_value,
        cagr_years=cagr_years,
    )


def average_two_periods(
    series: CanonicalFinancialSeries,
    metric: CanonicalMetric,
    *,
    current_offset: int = 0,
    prior_offset: int = 1,
) -> Decimal:
    current = _value(series, metric, year_offset=current_offset)
    prior = _value(series, metric, year_offset=prior_offset)

    if current is None or prior is None:
        raise LookupError(
            f"{metric.value} requires values for offsets "
            f"{current_offset} and {prior_offset}"
        )

    return (current + prior) / Decimal(2)


def _value(
    series: CanonicalFinancialSeries,
    metric: CanonicalMetric,
    *,
    year_offset: int,
) -> Decimal | None:
    financials = series.get(year_offset)
    if financials is None:
        return None

    fact = financials.get(metric)
    return fact.value if fact is not None else None


def _growth_rate(current: Decimal, prior: Decimal) -> float | None:
    if prior <= 0:
        return None
    return float((current / prior) - Decimal(1))
