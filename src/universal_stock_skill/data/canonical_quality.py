from __future__ import annotations

from pydantic import BaseModel

from universal_stock_skill.data.canonical import (
    CanonicalFinancialSet,
    CanonicalMetric,
    MappingMatchType,
)


class CanonicalMappingQuality(BaseModel):
    requested_count: int
    mapped_count: int
    exact_count: int
    fallback_count: int
    missing_count: int
    coverage_ratio: float
    fallback_ratio: float
    fallback_metrics: list[CanonicalMetric]
    missing_metrics: list[CanonicalMetric]


def evaluate_mapping_quality(
    financials: CanonicalFinancialSet,
) -> CanonicalMappingQuality:
    exact = [
        fact
        for fact in financials.facts
        if fact.match_type == MappingMatchType.STANDARD_EXACT
    ]
    fallback = [
        fact
        for fact in financials.facts
        if fact.match_type == MappingMatchType.EXTENSION_FALLBACK
    ]

    mapped_count = len(financials.facts)
    missing_count = len(financials.missing)
    requested_count = mapped_count + missing_count

    coverage_ratio = (
        mapped_count / requested_count
        if requested_count
        else 1.0
    )
    fallback_ratio = (
        len(fallback) / mapped_count
        if mapped_count
        else 0.0
    )

    return CanonicalMappingQuality(
        requested_count=requested_count,
        mapped_count=mapped_count,
        exact_count=len(exact),
        fallback_count=len(fallback),
        missing_count=missing_count,
        coverage_ratio=coverage_ratio,
        fallback_ratio=fallback_ratio,
        fallback_metrics=[fact.metric for fact in fallback],
        missing_metrics=list(financials.missing),
    )
