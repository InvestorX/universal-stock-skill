from decimal import Decimal

import pytest

from universal_stock_skill.data.canonical import (
    AccountingStandard,
    CanonicalMappingConflict,
    CanonicalMetric,
    ConsolidationPreference,
)
from universal_stock_skill.data.canonical_mappings import DEFAULT_CANONICAL_MAPPER
from universal_stock_skill.data.edinet_csv import EDINETCsvFact


def fact(
    element_id: str,
    value: str,
    *,
    item_name: str = "項目",
    context_id: str = "CurrentYearDuration",
    relative_year: str = "当期",
    consolidation: str = "連結",
    period_type: str = "期間",
    unit: str = "円",
    source_file: str = "facts.csv",
    row_number: int = 2,
) -> EDINETCsvFact:
    return EDINETCsvFact(
        element_id=element_id,
        item_name=item_name,
        context_id=context_id,
        relative_year=relative_year,
        consolidation=consolidation,
        period_type=period_type,
        unit_id="JPY",
        unit=unit,
        raw_value=value,
        source_file=source_file,
        row_number=row_number,
    )


def test_jgaap_core_metrics_are_mapped_to_canonical_names() -> None:
    facts = [
        fact("jpcrp_cor:NetSalesSummaryOfBusinessResults", "1000", item_name="売上高"),
        fact("jppfs_cor:OperatingIncome", "120", item_name="営業利益"),
        fact(
            "jppfs_cor:ProfitLossAttributableToOwnersOfParent",
            "80",
            item_name="親会社株主に帰属する当期純利益",
        ),
        fact(
            "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults",
            "55.5",
            item_name="1株当たり当期純利益",
        ),
    ]

    result = DEFAULT_CANONICAL_MAPPER.resolve(
        facts,
        metrics=[
            CanonicalMetric.REVENUE,
            CanonicalMetric.OPERATING_INCOME,
            CanonicalMetric.NET_INCOME,
            CanonicalMetric.EPS,
        ],
    )

    assert result.missing == []
    assert result.get(CanonicalMetric.REVENUE).value == Decimal(1000)
    assert result.get(CanonicalMetric.OPERATING_INCOME).value == Decimal(120)
    assert result.get(CanonicalMetric.NET_INCOME).value == Decimal(80)
    assert result.get(CanonicalMetric.EPS).value == Decimal("55.5")
    assert (
        result.get(CanonicalMetric.OPERATING_INCOME).accounting_standard
        == AccountingStandard.JGAAP
    )


def test_ifrs_aliases_resolve_to_same_canonical_metrics() -> None:
    facts = [
        fact("jpcrp_cor:RevenueIFRSSummaryOfBusinessResults", "2000"),
        fact("jpigp_cor:OperatingProfitLossIFRS", "250"),
        fact(
            "jpcrp_cor:ProfitLossAttributableToOwnersOfParentIFRSSummaryOfBusinessResults",
            "180",
        ),
    ]

    result = DEFAULT_CANONICAL_MAPPER.resolve(
        facts,
        metrics=[
            CanonicalMetric.REVENUE,
            CanonicalMetric.OPERATING_INCOME,
            CanonicalMetric.NET_INCOME,
        ],
    )

    assert result.missing == []
    assert all(
        item.accounting_standard == AccountingStandard.IFRS
        for item in result.facts
    )


def test_current_year_is_preferred_and_prior_year_is_filtered() -> None:
    facts = [
        fact(
            "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "1000",
            context_id="CurrentYearDuration",
            relative_year="当期",
        ),
        fact(
            "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "900",
            context_id="Prior1YearDuration",
            relative_year="前期",
            row_number=3,
        ),
    ]

    resolved = DEFAULT_CANONICAL_MAPPER.resolve_metric(
        facts,
        CanonicalMetric.REVENUE,
    )

    assert resolved is not None
    assert resolved.value == Decimal(1000)


def test_auto_scope_prefers_consolidated_over_non_consolidated() -> None:
    facts = [
        fact("jpcrp_cor:NetSalesSummaryOfBusinessResults", "1000"),
        fact(
            "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "700",
            consolidation="個別",
            context_id="CurrentYearDuration_NonConsolidatedMember",
            row_number=3,
        ),
    ]

    auto = DEFAULT_CANONICAL_MAPPER.resolve_metric(
        facts,
        CanonicalMetric.REVENUE,
    )
    non_consolidated = DEFAULT_CANONICAL_MAPPER.resolve_metric(
        facts,
        CanonicalMetric.REVENUE,
        consolidation=ConsolidationPreference.NON_CONSOLIDATED,
    )

    assert auto is not None
    assert non_consolidated is not None
    assert auto.value == Decimal(1000)
    assert non_consolidated.value == Decimal(700)


def test_industry_revenue_proxy_keeps_semantic_note() -> None:
    resolved = DEFAULT_CANONICAL_MAPPER.resolve_metric(
        [
            fact(
                "jpcrp_cor:OrdinaryIncomeSummaryOfBusinessResults",
                "5000",
                item_name="経常収益",
            )
        ],
        CanonicalMetric.REVENUE,
    )

    assert resolved is not None
    assert resolved.semantic_note is not None
    assert "financial institutions" in resolved.semantic_note


def test_equal_priority_conflicting_facts_raise_instead_of_guessing() -> None:
    facts = [
        fact(
            "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "1000",
            source_file="a.csv",
        ),
        fact(
            "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "1100",
            source_file="b.csv",
            row_number=4,
        ),
    ]

    with pytest.raises(CanonicalMappingConflict):
        DEFAULT_CANONICAL_MAPPER.resolve_metric(
            facts,
            CanonicalMetric.REVENUE,
        )
