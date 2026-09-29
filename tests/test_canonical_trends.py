from decimal import Decimal

import pytest

from universal_stock_skill.analysis.trends import (
    average_two_periods,
    calculate_canonical_trend,
    calculate_canonical_trends,
)
from universal_stock_skill.data.canonical import (
    AccountingStandard,
    CanonicalFinancialFact,
    CanonicalFinancialPeriod,
    CanonicalFinancialSeries,
    CanonicalFinancialSet,
    CanonicalMetric,
    MappingMatchType,
)


def financial_fact(
    metric: CanonicalMetric,
    value: str,
) -> CanonicalFinancialFact:
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


def period(
    year_offset: int,
    values: dict[CanonicalMetric, str],
) -> CanonicalFinancialPeriod:
    return CanonicalFinancialPeriod(
        year_offset=year_offset,
        financials=CanonicalFinancialSet(
            facts=[
                financial_fact(metric, value)
                for metric, value in values.items()
            ],
            missing=[],
        ),
    )


def test_trend_calculates_yoy_and_oldest_available_cagr() -> None:
    series = CanonicalFinancialSeries(
        periods=[
            period(0, {CanonicalMetric.REVENUE: "121"}),
            period(1, {CanonicalMetric.REVENUE: "110"}),
            period(2, {CanonicalMetric.REVENUE: "100"}),
        ]
    )

    trend = calculate_canonical_trend(series, CanonicalMetric.REVENUE)

    assert trend is not None
    assert trend.current_value == Decimal(121)
    assert trend.prior_value == Decimal(110)
    assert trend.year_over_year == pytest.approx(0.10)
    assert trend.cagr_value == pytest.approx(0.10)
    assert trend.cagr_years == 2


def test_negative_profit_does_not_produce_misleading_cagr() -> None:
    series = CanonicalFinancialSeries(
        periods=[
            period(0, {CanonicalMetric.NET_INCOME: "20"}),
            period(1, {CanonicalMetric.NET_INCOME: "-10"}),
        ]
    )

    trend = calculate_canonical_trend(series, CanonicalMetric.NET_INCOME)

    assert trend is not None
    assert trend.year_over_year == pytest.approx(-3.0)
    assert trend.cagr_value is None
    assert trend.cagr_years is None


def test_zero_prior_value_makes_yoy_unavailable() -> None:
    series = CanonicalFinancialSeries(
        periods=[
            period(0, {CanonicalMetric.OPERATING_INCOME: "10"}),
            period(1, {CanonicalMetric.OPERATING_INCOME: "0"}),
        ]
    )

    trend = calculate_canonical_trend(
        series,
        CanonicalMetric.OPERATING_INCOME,
    )

    assert trend is not None
    assert trend.year_over_year is None


def test_average_two_periods_is_generic_not_roe_specific() -> None:
    series = CanonicalFinancialSeries(
        periods=[
            period(0, {CanonicalMetric.NET_ASSETS: "120"}),
            period(1, {CanonicalMetric.NET_ASSETS: "100"}),
        ]
    )

    assert average_two_periods(
        series,
        CanonicalMetric.NET_ASSETS,
    ) == Decimal(110)


def test_trend_set_reports_missing_metrics() -> None:
    series = CanonicalFinancialSeries(
        periods=[period(0, {CanonicalMetric.REVENUE: "100"})]
    )

    result = calculate_canonical_trends(
        series,
        [CanonicalMetric.REVENUE, CanonicalMetric.NET_INCOME],
    )

    assert result.get(CanonicalMetric.REVENUE) is not None
    assert result.missing == [CanonicalMetric.NET_INCOME]
