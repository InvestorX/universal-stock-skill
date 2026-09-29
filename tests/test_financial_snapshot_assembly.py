from datetime import UTC, datetime
from decimal import Decimal

import pytest

from universal_stock_skill.analysis.assembly import (
    FinancialSnapshotAssemblyError,
    assemble_financial_snapshot,
)
from universal_stock_skill.analysis.workflow import calculate_stock_metrics
from universal_stock_skill.data.canonical import (
    AccountingStandard,
    CanonicalFinancialFact,
    CanonicalFinancialPeriod,
    CanonicalFinancialSeries,
    CanonicalFinancialSet,
    CanonicalMetric,
    MappingMatchType,
)
from universal_stock_skill.data.market import MarketSnapshot


def fact(
    metric: CanonicalMetric,
    value: str,
    *,
    unit: str = "円",
) -> CanonicalFinancialFact:
    return CanonicalFinancialFact(
        metric=metric,
        value=Decimal(value),
        unit=unit,
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


def current_financials() -> CanonicalFinancialSet:
    return CanonicalFinancialSet(
        facts=[
            fact(CanonicalMetric.REVENUE, "1000"),
            fact(CanonicalMetric.OPERATING_INCOME, "120"),
            fact(CanonicalMetric.PROFIT_BEFORE_TAX, "100"),
            fact(CanonicalMetric.INCOME_TAXES, "30"),
            fact(CanonicalMetric.NET_INCOME, "70"),
            fact(CanonicalMetric.EPS, "10"),
            fact(CanonicalMetric.BPS, "100"),
            fact(CanonicalMetric.ROE_OFFICIAL, "0.10", unit="pure"),
            fact(CanonicalMetric.CF_OPERATING, "150"),
            fact(CanonicalMetric.CAPEX_PPE, "-40"),
            fact(CanonicalMetric.CAPEX_INTANGIBLE, "-10"),
        ],
        missing=[],
    )


def test_assembly_builds_snapshot_and_metrics_without_manual_derived_inputs() -> None:
    current = current_financials()
    series = CanonicalFinancialSeries(
        periods=[
            CanonicalFinancialPeriod(
                year_offset=0,
                financials=current,
            )
        ]
    )
    market = MarketSnapshot(
        symbol="7203",
        observed_at=datetime(2026, 9, 29, 6, 30, tzinfo=UTC),
        price=120,
        currency="JPY",
        source="fixture",
        market_cap=12_000,
    )

    result = assemble_financial_snapshot(current, series, market)
    metrics = calculate_stock_metrics(result.snapshot)

    assert result.snapshot.average_equity == 700
    assert result.snapshot.capital_expenditure == 50
    assert result.snapshot.nopat == pytest.approx(84)
    assert metrics.per == pytest.approx(12)
    assert metrics.pbr == pytest.approx(1.2)
    assert metrics.roe == pytest.approx(0.1)
    assert metrics.free_cash_flow == pytest.approx(100)
    assert metrics.free_cash_flow_yield == pytest.approx(100 / 12_000)
    assert metrics.roic is None


def test_assembly_requires_safe_average_equity_derivation() -> None:
    current = current_financials()
    current = current.model_copy(
        update={
            "facts": [
                item
                for item in current.facts
                if item.metric != CanonicalMetric.ROE_OFFICIAL
            ]
        }
    )
    series = CanonicalFinancialSeries(
        periods=[
            CanonicalFinancialPeriod(year_offset=0, financials=current)
        ]
    )
    market = MarketSnapshot(
        symbol="7203",
        observed_at=datetime(2026, 9, 29, 6, 30, tzinfo=UTC),
        price=120,
        currency="JPY",
        source="fixture",
        market_cap=12_000,
    )

    with pytest.raises(
        FinancialSnapshotAssemblyError,
        match="average_equity",
    ):
        assemble_financial_snapshot(current, series, market)
