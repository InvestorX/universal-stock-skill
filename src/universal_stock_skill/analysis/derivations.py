from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

from universal_stock_skill.data.canonical import (
    AccountingStandard,
    CanonicalFinancialFact,
    CanonicalFinancialSeries,
    CanonicalFinancialSet,
    CanonicalMetric,
)


class DerivationMethod(StrEnum):
    OFFICIAL_ROE_BACKSOLVE = "official_roe_backsolve"
    TWO_PERIOD_OWNERS_EQUITY = "two_period_owners_equity"
    CAPEX_TOTAL_FACT = "capex_total_fact"
    CAPEX_COMPONENT_SUM = "capex_component_sum"
    EFFECTIVE_TAX_RATE = "effective_tax_rate"
    UNAVAILABLE = "unavailable"


class DerivedFinancialInputs(BaseModel):
    average_equity: Decimal | None = None
    average_equity_method: DerivationMethod = DerivationMethod.UNAVAILABLE
    capital_expenditure: Decimal | None = None
    capital_expenditure_method: DerivationMethod = DerivationMethod.UNAVAILABLE
    effective_tax_rate: Decimal | None = None
    nopat: Decimal | None = None
    nopat_method: DerivationMethod = DerivationMethod.UNAVAILABLE
    average_invested_capital: Decimal | None = None
    average_invested_capital_method: DerivationMethod = DerivationMethod.UNAVAILABLE


def derive_financial_inputs(
    current: CanonicalFinancialSet,
    series: CanonicalFinancialSeries,
) -> DerivedFinancialInputs:
    average_equity, average_equity_method = derive_average_equity(current, series)
    capex, capex_method = derive_capital_expenditure(current)
    tax_rate, nopat = derive_nopat(current)

    return DerivedFinancialInputs(
        average_equity=average_equity,
        average_equity_method=average_equity_method,
        capital_expenditure=capex,
        capital_expenditure_method=capex_method,
        effective_tax_rate=tax_rate,
        nopat=nopat,
        nopat_method=(
            DerivationMethod.EFFECTIVE_TAX_RATE
            if nopat is not None
            else DerivationMethod.UNAVAILABLE
        ),
    )


def derive_average_equity(
    current: CanonicalFinancialSet,
    series: CanonicalFinancialSeries,
) -> tuple[Decimal | None, DerivationMethod]:
    net_income = current.get(CanonicalMetric.NET_INCOME)
    roe = current.get(CanonicalMetric.ROE_OFFICIAL)

    if net_income is not None and roe is not None:
        ratio = normalize_ratio(roe)
        if ratio is not None and ratio > 0:
            return (
                net_income.value / ratio,
                DerivationMethod.OFFICIAL_ROE_BACKSOLVE,
            )

    current_net_assets = _series_fact(series, CanonicalMetric.NET_ASSETS, 0)
    prior_net_assets = _series_fact(series, CanonicalMetric.NET_ASSETS, 1)

    if (
        current_net_assets is not None
        and prior_net_assets is not None
        and _owners_equity_compatible(current_net_assets)
        and _owners_equity_compatible(prior_net_assets)
    ):
        return (
            (current_net_assets.value + prior_net_assets.value) / Decimal(2),
            DerivationMethod.TWO_PERIOD_OWNERS_EQUITY,
        )

    return None, DerivationMethod.UNAVAILABLE


def derive_capital_expenditure(
    current: CanonicalFinancialSet,
) -> tuple[Decimal | None, DerivationMethod]:
    total = current.get(CanonicalMetric.CAPEX_TOTAL)
    if total is not None:
        return abs(total.value), DerivationMethod.CAPEX_TOTAL_FACT

    components = [
        current.get(CanonicalMetric.CAPEX_PPE),
        current.get(CanonicalMetric.CAPEX_INTANGIBLE),
    ]
    available = [fact for fact in components if fact is not None]
    if not available:
        return None, DerivationMethod.UNAVAILABLE

    return (
        sum((abs(fact.value) for fact in available), start=Decimal(0)),
        DerivationMethod.CAPEX_COMPONENT_SUM,
    )


def derive_nopat(
    current: CanonicalFinancialSet,
) -> tuple[Decimal | None, Decimal | None]:
    operating_income = current.get(CanonicalMetric.OPERATING_INCOME)
    profit_before_tax = current.get(CanonicalMetric.PROFIT_BEFORE_TAX)
    income_taxes = current.get(CanonicalMetric.INCOME_TAXES)

    if (
        operating_income is None
        or profit_before_tax is None
        or income_taxes is None
        or profit_before_tax.value <= 0
        or income_taxes.value < 0
    ):
        return None, None

    tax_rate = income_taxes.value / profit_before_tax.value
    if tax_rate < 0 or tax_rate > 1:
        return None, None

    nopat = operating_income.value * (Decimal(1) - tax_rate)
    return tax_rate, nopat


def normalize_ratio(fact: CanonicalFinancialFact) -> Decimal | None:
    value = fact.value
    if value < 0:
        return None

    if value <= 1:
        return value

    unit = fact.unit.strip().lower()
    if any(token in unit for token in ("%", "％", "percent", "percentage")):
        if value <= 100:
            return value / Decimal(100)

    return None


def _series_fact(
    series: CanonicalFinancialSeries,
    metric: CanonicalMetric,
    year_offset: int,
) -> CanonicalFinancialFact | None:
    financials = series.get(year_offset)
    return financials.get(metric) if financials is not None else None


def _owners_equity_compatible(fact: CanonicalFinancialFact) -> bool:
    return fact.accounting_standard in {
        AccountingStandard.IFRS,
        AccountingStandard.USGAAP,
    }
