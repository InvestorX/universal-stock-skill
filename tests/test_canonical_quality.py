from decimal import Decimal

import pytest

from universal_stock_skill.data.canonical import (
    AccountingStandard,
    CanonicalFinancialFact,
    CanonicalFinancialSet,
    CanonicalMetric,
    MappingMatchType,
)
from universal_stock_skill.data.canonical_quality import evaluate_mapping_quality


def fact(
    metric: CanonicalMetric,
    match_type: MappingMatchType,
) -> CanonicalFinancialFact:
    return CanonicalFinancialFact(
        metric=metric,
        value=Decimal(100),
        unit="円",
        accounting_standard=AccountingStandard.JGAAP,
        match_type=match_type,
        element_id=f"demo:{metric.value}",
        item_name=metric.value,
        context_id="CurrentYearDuration",
        relative_year="当期",
        consolidation="連結",
        period_type="期間",
        source_file="facts.csv",
        row_number=2,
    )


def test_mapping_quality_separates_exact_fallback_and_missing() -> None:
    financials = CanonicalFinancialSet(
        facts=[
            fact(CanonicalMetric.REVENUE, MappingMatchType.STANDARD_EXACT),
            fact(
                CanonicalMetric.OPERATING_INCOME,
                MappingMatchType.EXTENSION_FALLBACK,
            ),
        ],
        missing=[CanonicalMetric.NET_INCOME, CanonicalMetric.EPS],
    )

    quality = evaluate_mapping_quality(financials)

    assert quality.requested_count == 4
    assert quality.mapped_count == 2
    assert quality.exact_count == 1
    assert quality.fallback_count == 1
    assert quality.missing_count == 2
    assert quality.coverage_ratio == pytest.approx(0.5)
    assert quality.fallback_ratio == pytest.approx(0.5)
    assert quality.fallback_metrics == [CanonicalMetric.OPERATING_INCOME]
    assert quality.missing_metrics == [
        CanonicalMetric.NET_INCOME,
        CanonicalMetric.EPS,
    ]


def test_empty_request_is_full_coverage_without_fallback() -> None:
    quality = evaluate_mapping_quality(
        CanonicalFinancialSet(facts=[], missing=[])
    )

    assert quality.coverage_ratio == 1.0
    assert quality.fallback_ratio == 0.0
