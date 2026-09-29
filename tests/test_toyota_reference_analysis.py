from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from universal_stock_skill.analysis.derivations import DerivationMethod
from universal_stock_skill.benchmark.toyota_analysis import (
    analyze_toyota_reference,
    toyota_reference_canonical_financials,
    toyota_reference_market_snapshot,
)
from universal_stock_skill.data.canonical import CanonicalMetric


JST = ZoneInfo("Asia/Tokyo")


def test_toyota_reference_canonical_values_use_base_jpy_units() -> None:
    current, series = toyota_reference_canonical_financials()

    assert current.get(CanonicalMetric.REVENUE).value == Decimal(
        50_684_952_000_000
    )
    assert current.get(CanonicalMetric.NET_INCOME).value == Decimal(
        3_848_098_000_000
    )
    assert current.get(CanonicalMetric.EPS).value == Decimal("295.25")
    assert current.get(CanonicalMetric.BPS).value == Decimal("3062.82")
    assert current.get(CanonicalMetric.CAPEX_TOTAL).value == Decimal(
        -5_293_348_000_000
    )
    assert (
        series.get(1).get(CanonicalMetric.NET_ASSETS).value
        == Decimal(35_924_826_000_000)
    )


def test_toyota_reference_analysis_reuses_existing_finance_pipeline() -> None:
    market = toyota_reference_market_snapshot(
        price=3000,
        observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
    )

    result = analyze_toyota_reference(market)

    assert result.assembly.derived.average_equity == Decimal(
        37_921_840_000_000
    )
    assert (
        result.assembly.derived.average_equity_method
        == DerivationMethod.TWO_PERIOD_OWNERS_EQUITY
    )
    assert result.assembly.derived.capital_expenditure == Decimal(
        5_293_348_000_000
    )
    assert (
        result.assembly.derived.capital_expenditure_method
        == DerivationMethod.CAPEX_TOTAL_FACT
    )

    snapshot = result.assembly.snapshot
    assert snapshot.operating_cash_flow == 5_472_920_000_000
    assert snapshot.capital_expenditure == 5_293_348_000_000

    assert result.metrics.operating_margin == pytest.approx(0.0743063937)
    assert result.metrics.per == pytest.approx(10.16088061)
    assert result.metrics.pbr == pytest.approx(0.97948949)
    assert result.metrics.roe == pytest.approx(0.101474454)
    assert result.metrics.free_cash_flow == pytest.approx(179_572_000_000)
    assert result.metrics.free_cash_flow_yield == pytest.approx(
        0.00459261625
    )
    assert result.metrics.roic is None


def test_toyota_reference_market_cap_uses_end_of_year_net_shares() -> None:
    market = toyota_reference_market_snapshot(
        price=3000,
        observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
    )

    assert market.shares_outstanding == 13_033_384_474
    assert market.market_cap == 39_100_153_422_000


def test_toyota_reference_trends_use_real_fy2025_comparatives() -> None:
    result = analyze_toyota_reference(
        toyota_reference_market_snapshot(
            price=3000,
            observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
        )
    )

    revenue = result.trends.get(CanonicalMetric.REVENUE)
    operating_income = result.trends.get(CanonicalMetric.OPERATING_INCOME)
    net_income = result.trends.get(CanonicalMetric.NET_INCOME)

    assert revenue.year_over_year == pytest.approx(0.05512968, rel=1e-5)
    assert operating_income.year_over_year == pytest.approx(-0.21464947, rel=1e-5)
    assert net_income.year_over_year == pytest.approx(-0.19243892, rel=1e-5)


def test_toyota_reference_analysis_rejects_future_market_data() -> None:
    market = toyota_reference_market_snapshot(
        price=3000,
        observed_at=datetime(2026, 9, 30, 15, 30, tzinfo=JST),
    )

    with pytest.raises(ValueError, match="newer than Toyota reference-case as_of"):
        analyze_toyota_reference(market)
