from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from universal_stock_skill.analysis.assembly import (
    FinancialSnapshotAssemblyResult,
    assemble_financial_snapshot,
)
from universal_stock_skill.analysis.models import StockMetrics
from universal_stock_skill.analysis.trends import (
    CanonicalTrendSet,
    calculate_canonical_trends,
)
from universal_stock_skill.analysis.workflow import calculate_stock_metrics
from universal_stock_skill.benchmark.toyota import (
    TOYOTA_FY2026_SUMMARY_URL,
    toyota_7203_reference_case,
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
from universal_stock_skill.data.market import MarketSnapshot
from universal_stock_skill.evidence.collection import EvidenceItem


MILLION_YEN = Decimal(1_000_000)

TOYOTA_REFERENCE_TREND_METRICS = [
    CanonicalMetric.REVENUE,
    CanonicalMetric.OPERATING_INCOME,
    CanonicalMetric.NET_INCOME,
    CanonicalMetric.EPS,
    CanonicalMetric.CF_OPERATING,
]


class ToyotaReferenceAnalysis(BaseModel):
    case_id: str
    current: CanonicalFinancialSet
    series: CanonicalFinancialSeries
    market: MarketSnapshot
    assembly: FinancialSnapshotAssemblyResult
    trends: CanonicalTrendSet
    metrics: StockMetrics
    evidence: list[EvidenceItem]


def toyota_reference_market_snapshot(
    *,
    price: float,
    observed_at: datetime,
) -> MarketSnapshot:
    case = toyota_7203_reference_case()
    current = case.period("FY2026")
    return MarketSnapshot(
        symbol=case.symbol,
        observed_at=observed_at,
        price=price,
        currency="JPY",
        source="reference:toyota-market-input",
        shares_outstanding=float(current.share_counts["outstanding_end"]),
    )


def toyota_reference_canonical_financials(
) -> tuple[CanonicalFinancialSet, CanonicalFinancialSeries]:
    case = toyota_7203_reference_case()
    current_period = case.period("FY2026")
    prior_period = case.period("FY2025")

    current = CanonicalFinancialSet(
        facts=[
            _money_fact(
                CanonicalMetric.REVENUE,
                current_period.values_million_yen["revenue"],
                year_offset=0,
            ),
            _money_fact(
                CanonicalMetric.OPERATING_INCOME,
                current_period.values_million_yen["operating_income"],
                year_offset=0,
            ),
            _money_fact(
                CanonicalMetric.PROFIT_BEFORE_TAX,
                current_period.values_million_yen["profit_before_tax"],
                year_offset=0,
            ),
            _money_fact(
                CanonicalMetric.NET_INCOME,
                current_period.values_million_yen[
                    "net_income_attributable_to_parent"
                ],
                year_offset=0,
                semantic_note=(
                    "Net income attributable to Toyota Motor Corporation; "
                    "aligned with EPS and ROE."
                ),
            ),
            _money_fact(
                CanonicalMetric.TOTAL_ASSETS,
                current_period.values_million_yen["total_assets"],
                year_offset=0,
                period_type="時点",
            ),
            _money_fact(
                CanonicalMetric.NET_ASSETS,
                current_period.values_million_yen["owners_equity"],
                year_offset=0,
                period_type="時点",
                semantic_note="Toyota Motor Corporation shareholders' equity.",
            ),
            _per_share_fact(
                CanonicalMetric.EPS,
                current_period.per_share_yen["eps_basic"],
                year_offset=0,
            ),
            _per_share_fact(
                CanonicalMetric.DILUTED_EPS,
                current_period.per_share_yen["eps_diluted"],
                year_offset=0,
            ),
            _per_share_fact(
                CanonicalMetric.BPS,
                current_period.per_share_yen["bps"],
                year_offset=0,
                period_type="時点",
            ),
            _ratio_fact(
                CanonicalMetric.ROE_OFFICIAL,
                current_period.ratios["roe"],
                year_offset=0,
            ),
            _ratio_fact(
                CanonicalMetric.EQUITY_RATIO_OFFICIAL,
                current_period.ratios["owners_equity_ratio"],
                year_offset=0,
                period_type="時点",
            ),
            _money_fact(
                CanonicalMetric.CF_OPERATING,
                current_period.values_million_yen["operating_cash_flow"],
                year_offset=0,
            ),
            _money_fact(
                CanonicalMetric.INCOME_TAXES,
                current_period.values_million_yen["income_tax_expense"],
                year_offset=0,
            ),
            _money_fact(
                CanonicalMetric.CAPEX_TOTAL,
                -current_period.values_million_yen["capex_cash_outflow"],
                year_offset=0,
                semantic_note=(
                    "Cash-flow CapEx: fixed assets excluding leased equipment "
                    "+ equipment leased to others + intangible assets."
                ),
            ),
        ],
        missing=[],
    )

    prior = CanonicalFinancialSet(
        facts=[
            _money_fact(
                CanonicalMetric.REVENUE,
                prior_period.values_million_yen["revenue"],
                year_offset=1,
            ),
            _money_fact(
                CanonicalMetric.OPERATING_INCOME,
                prior_period.values_million_yen["operating_income"],
                year_offset=1,
            ),
            _money_fact(
                CanonicalMetric.PROFIT_BEFORE_TAX,
                prior_period.values_million_yen["profit_before_tax"],
                year_offset=1,
            ),
            _money_fact(
                CanonicalMetric.NET_INCOME,
                prior_period.values_million_yen[
                    "net_income_attributable_to_parent"
                ],
                year_offset=1,
            ),
            _money_fact(
                CanonicalMetric.TOTAL_ASSETS,
                prior_period.values_million_yen["total_assets"],
                year_offset=1,
                period_type="時点",
            ),
            _money_fact(
                CanonicalMetric.NET_ASSETS,
                prior_period.values_million_yen["owners_equity"],
                year_offset=1,
                period_type="時点",
                semantic_note="Toyota Motor Corporation shareholders' equity.",
            ),
            _per_share_fact(
                CanonicalMetric.EPS,
                prior_period.per_share_yen["eps_basic"],
                year_offset=1,
            ),
            _per_share_fact(
                CanonicalMetric.BPS,
                prior_period.per_share_yen["bps"],
                year_offset=1,
                period_type="時点",
            ),
            _ratio_fact(
                CanonicalMetric.ROE_OFFICIAL,
                prior_period.ratios["roe"],
                year_offset=1,
            ),
            _money_fact(
                CanonicalMetric.CF_OPERATING,
                prior_period.values_million_yen["operating_cash_flow"],
                year_offset=1,
            ),
        ],
        missing=[],
    )

    return (
        current,
        CanonicalFinancialSeries(
            periods=[
                CanonicalFinancialPeriod(
                    year_offset=0,
                    financials=current,
                ),
                CanonicalFinancialPeriod(
                    year_offset=1,
                    financials=prior,
                ),
            ]
        ),
    )


def analyze_toyota_reference(
    market: MarketSnapshot,
) -> ToyotaReferenceAnalysis:
    case = toyota_7203_reference_case()
    if market.symbol.strip().upper() != case.symbol:
        raise ValueError("Toyota reference analysis requires symbol 7203")
    if market.observed_at > case.as_of:
        raise ValueError("market snapshot is newer than Toyota reference-case as_of")

    current, series = toyota_reference_canonical_financials()
    assembly = assemble_financial_snapshot(current, series, market)
    trends = calculate_canonical_trends(
        series,
        TOYOTA_REFERENCE_TREND_METRICS,
    )
    metrics = calculate_stock_metrics(assembly.snapshot)

    return ToyotaReferenceAnalysis(
        case_id=case.case_id,
        current=current,
        series=series,
        market=market,
        assembly=assembly,
        trends=trends,
        metrics=metrics,
        evidence=case.qualitative_evidence,
    )


def _money_fact(
    metric: CanonicalMetric,
    value_million_yen: Decimal,
    *,
    year_offset: int,
    period_type: str = "期間",
    semantic_note: str | None = None,
) -> CanonicalFinancialFact:
    return _fact(
        metric,
        value_million_yen * MILLION_YEN,
        unit="JPY",
        year_offset=year_offset,
        period_type=period_type,
        semantic_note=semantic_note,
    )


def _per_share_fact(
    metric: CanonicalMetric,
    value_yen: Decimal,
    *,
    year_offset: int,
    period_type: str = "期間",
) -> CanonicalFinancialFact:
    return _fact(
        metric,
        value_yen,
        unit="JPYPerShare",
        year_offset=year_offset,
        period_type=period_type,
    )


def _ratio_fact(
    metric: CanonicalMetric,
    value: Decimal,
    *,
    year_offset: int,
    period_type: str = "期間",
) -> CanonicalFinancialFact:
    return _fact(
        metric,
        value,
        unit="pure",
        year_offset=year_offset,
        period_type=period_type,
    )


def _fact(
    metric: CanonicalMetric,
    value: Decimal,
    *,
    unit: str,
    year_offset: int,
    period_type: str,
    semantic_note: str | None = None,
) -> CanonicalFinancialFact:
    current = year_offset == 0
    return CanonicalFinancialFact(
        metric=metric,
        value=value,
        unit=unit,
        accounting_standard=AccountingStandard.IFRS,
        match_type=MappingMatchType.STANDARD_EXACT,
        element_id=f"toyota_ir:{metric.value}",
        item_name=metric.value,
        context_id=(
            ("CurrentYearInstant" if period_type == "時点" else "CurrentYearDuration")
            if current
            else (
                f"Prior{year_offset}YearInstant"
                if period_type == "時点"
                else f"Prior{year_offset}YearDuration"
            )
        ),
        relative_year="当期" if current else "前期",
        consolidation="連結",
        period_type=period_type,
        source_file=TOYOTA_FY2026_SUMMARY_URL,
        row_number=1,
        semantic_note=semantic_note,
    )
