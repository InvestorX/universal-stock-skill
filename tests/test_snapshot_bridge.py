from datetime import UTC, datetime
from decimal import Decimal

import pytest

from universal_stock_skill.analysis.bridge import (
    MissingCanonicalMetric,
    SnapshotBridgeInputs,
    build_financial_snapshot,
)
from universal_stock_skill.data.canonical import (
    AccountingStandard,
    CanonicalFinancialFact,
    CanonicalFinancialSet,
    CanonicalMetric,
    MappingMatchType,
)


def canonical_fact(metric: CanonicalMetric, value: str) -> CanonicalFinancialFact:
    return CanonicalFinancialFact(
        metric=metric,
        value=Decimal(value),
        unit="円",
        accounting_standard=AccountingStandard.JGAAP,
        match_type=MappingMatchType.STANDARD_EXACT,
        element_id=f"demo:{metric.value}",
        item_name=metric.value,
        context_id="CurrentYearDuration",
        relative_year="当期",
        consolidation="連結",
        period_type="期間",
        source_file="facts.csv",
        row_number=2,
    )


def bridge_inputs() -> SnapshotBridgeInputs:
    return SnapshotBridgeInputs(
        symbol="7203",
        as_of=datetime(2026, 9, 1, tzinfo=UTC),
        price=3000,
        market_cap=40_000_000_000_000,
        average_equity=30_000_000_000_000,
        capital_expenditure=4_000_000_000_000,
    )


def test_build_financial_snapshot_from_canonical_set() -> None:
    canonical = CanonicalFinancialSet(
        facts=[
            canonical_fact(CanonicalMetric.REVENUE, "48000000000000"),
            canonical_fact(CanonicalMetric.OPERATING_INCOME, "6000000000000"),
            canonical_fact(CanonicalMetric.NET_INCOME, "5000000000000"),
            canonical_fact(CanonicalMetric.EPS, "320"),
            canonical_fact(CanonicalMetric.BPS, "2400"),
            canonical_fact(CanonicalMetric.CF_OPERATING, "7000000000000"),
        ],
        missing=[],
    )

    snapshot = build_financial_snapshot(canonical, bridge_inputs())

    assert snapshot.symbol == "7203"
    assert snapshot.revenue == 48_000_000_000_000
    assert snapshot.eps == 320
    assert snapshot.operating_cash_flow == 7_000_000_000_000


def test_missing_required_canonical_metric_raises() -> None:
    canonical = CanonicalFinancialSet(facts=[], missing=[CanonicalMetric.REVENUE])

    with pytest.raises(MissingCanonicalMetric):
        build_financial_snapshot(canonical, bridge_inputs())
