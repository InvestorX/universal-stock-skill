from decimal import Decimal

import pytest

from universal_stock_skill.analysis.derivations import (
    DerivationMethod,
    derive_average_equity,
    derive_capital_expenditure,
    derive_financial_inputs,
    derive_nopat,
    normalize_ratio,
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


def fact(
    metric: CanonicalMetric,
    value: str,
    *,
    unit: str = "円",
    standard: AccountingStandard = AccountingStandard.JGAAP,
) -> CanonicalFinancialFact:
    return CanonicalFinancialFact(
        metric=metric,
        value=Decimal(value),
        unit=unit,
        accounting_standard=standard,
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


def financials(
    *facts: CanonicalFinancialFact,
) -> CanonicalFinancialSet:
    return CanonicalFinancialSet(facts=list(facts), missing=[])


def series(
    current: CanonicalFinancialSet,
    prior: CanonicalFinancialSet | None = None,
) -> CanonicalFinancialSeries:
    periods = [CanonicalFinancialPeriod(year_offset=0, financials=current)]
    if prior is not None:
        periods.append(CanonicalFinancialPeriod(year_offset=1, financials=prior))
    return CanonicalFinancialSeries(periods=periods)


def test_average_equity_backsolves_official_roe_decimal() -> None:
    current = financials(
        fact(CanonicalMetric.NET_INCOME, "100"),
        fact(CanonicalMetric.ROE_OFFICIAL, "0.10", unit="pure"),
    )

    value, method = derive_average_equity(current, series(current))

    assert value == Decimal(1000)
    assert method == DerivationMethod.OFFICIAL_ROE_BACKSOLVE


def test_average_equity_accepts_percentage_style_roe() -> None:
    current = financials(
        fact(CanonicalMetric.NET_INCOME, "100"),
        fact(CanonicalMetric.ROE_OFFICIAL, "10", unit="%"),
    )

    value, method = derive_average_equity(current, series(current))

    assert value == Decimal(1000)
    assert method == DerivationMethod.OFFICIAL_ROE_BACKSOLVE


def test_average_equity_falls_back_to_ifrs_two_period_equity() -> None:
    current = financials(
        fact(
            CanonicalMetric.NET_ASSETS,
            "1200",
            standard=AccountingStandard.IFRS,
        )
    )
    prior = financials(
        fact(
            CanonicalMetric.NET_ASSETS,
            "1000",
            standard=AccountingStandard.IFRS,
        )
    )

    value, method = derive_average_equity(current, series(current, prior))

    assert value == Decimal(1100)
    assert method == DerivationMethod.TWO_PERIOD_OWNERS_EQUITY


def test_jgaap_net_assets_are_not_silently_used_as_average_equity() -> None:
    current = financials(fact(CanonicalMetric.NET_ASSETS, "1200"))
    prior = financials(fact(CanonicalMetric.NET_ASSETS, "1000"))

    value, method = derive_average_equity(current, series(current, prior))

    assert value is None
    assert method == DerivationMethod.UNAVAILABLE


def test_capex_total_fact_wins_over_components() -> None:
    current = financials(
        fact(CanonicalMetric.CAPEX_TOTAL, "-300"),
        fact(CanonicalMetric.CAPEX_PPE, "-250"),
        fact(CanonicalMetric.CAPEX_INTANGIBLE, "-80"),
    )

    value, method = derive_capital_expenditure(current)

    assert value == Decimal(300)
    assert method == DerivationMethod.CAPEX_TOTAL_FACT


def test_capex_sums_available_components_as_positive_outflow() -> None:
    current = financials(
        fact(CanonicalMetric.CAPEX_PPE, "-250"),
        fact(CanonicalMetric.CAPEX_INTANGIBLE, "80"),
    )

    value, method = derive_capital_expenditure(current)

    assert value == Decimal(330)
    assert method == DerivationMethod.CAPEX_COMPONENT_SUM


def test_nopat_uses_effective_tax_rate() -> None:
    current = financials(
        fact(CanonicalMetric.OPERATING_INCOME, "200"),
        fact(CanonicalMetric.PROFIT_BEFORE_TAX, "180"),
        fact(CanonicalMetric.INCOME_TAXES, "54"),
    )

    tax_rate, nopat = derive_nopat(current)

    assert tax_rate == Decimal("0.3")
    assert nopat == Decimal(140)


@pytest.mark.parametrize(
    ("pretax", "tax"),
    [
        ("0", "10"),
        ("-100", "10"),
        ("100", "-10"),
        ("100", "120"),
    ],
)
def test_nopat_rejects_unsafe_effective_tax_rates(pretax: str, tax: str) -> None:
    current = financials(
        fact(CanonicalMetric.OPERATING_INCOME, "200"),
        fact(CanonicalMetric.PROFIT_BEFORE_TAX, pretax),
        fact(CanonicalMetric.INCOME_TAXES, tax),
    )

    assert derive_nopat(current) == (None, None)


def test_ratio_normalization_rejects_ambiguous_large_pure_value() -> None:
    ratio = fact(CanonicalMetric.ROE_OFFICIAL, "10", unit="pure")

    assert normalize_ratio(ratio) is None


def test_derive_financial_inputs_leaves_invested_capital_unavailable() -> None:
    current = financials(
        fact(CanonicalMetric.NET_INCOME, "100"),
        fact(CanonicalMetric.ROE_OFFICIAL, "0.10", unit="pure"),
        fact(CanonicalMetric.CAPEX_PPE, "-50"),
        fact(CanonicalMetric.OPERATING_INCOME, "200"),
        fact(CanonicalMetric.PROFIT_BEFORE_TAX, "180"),
        fact(CanonicalMetric.INCOME_TAXES, "54"),
    )

    result = derive_financial_inputs(current, series(current))

    assert result.average_equity == Decimal(1000)
    assert result.capital_expenditure == Decimal(50)
    assert result.effective_tax_rate == Decimal("0.3")
    assert result.nopat == Decimal(140)
    assert result.average_invested_capital is None
    assert (
        result.average_invested_capital_method
        == DerivationMethod.UNAVAILABLE
    )
