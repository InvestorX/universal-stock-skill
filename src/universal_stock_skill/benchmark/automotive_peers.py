from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, model_validator

from universal_stock_skill.analysis.context import (
    AnalysisContext,
    add_peer_comparison_to_context,
)
from universal_stock_skill.analysis.peers import (
    PeerComparisonSet,
    PeerMetricRow,
)
from universal_stock_skill.benchmark.toyota_analysis import (
    ToyotaReferenceAnalysis,
    analyze_toyota_reference,
    toyota_reference_analysis_context,
)
from universal_stock_skill.data.canonical import CanonicalMetric
from universal_stock_skill.data.market import MarketSnapshot
from universal_stock_skill.evidence.collection import EvidenceItem
from universal_stock_skill.evidence.models import SourceRecord

JST = ZoneInfo("Asia/Tokyo")

HONDA_FY2026_RESULTS_URL = (
    "https://global.honda/en/investors/library/financialresult/main/08/"
    "teaserItems3/018/linkList/01/link/FYE202603_4Q_financial_result_e_1.pdf"
)
NISSAN_FY2025_RESULTS_URL = (
    "https://www.nissan-global.com/EN/IR/FINANCIAL_RESULTS/ASSETS/DATA/"
    "2025/20254th_financialresult_393_e.pdf"
)


class AutomotivePeerReference(BaseModel):
    symbol: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    issuer_fiscal_label: str = Field(min_length=1)
    period_end: date
    accounting_standard: str = Field(min_length=1)
    published_at: datetime
    revenue_million_yen: Decimal
    prior_revenue_million_yen: Decimal
    operating_income_million_yen: Decimal
    net_income_million_yen: Decimal
    eps_yen: Decimal
    bps_yen: Decimal
    roe: Decimal
    operating_margin: Decimal
    shares_outstanding: int
    operating_cash_flow_million_yen: Decimal | None = None
    cash_capex_million_yen: Decimal | None = None
    evidence: list[EvidenceItem]
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_reference(self) -> AutomotivePeerReference:
        if (
            self.published_at.tzinfo is None
            or self.published_at.utcoffset() is None
        ):
            raise ValueError("published_at must be timezone-aware")
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be positive")
        for item in self.evidence:
            if item.symbol != self.symbol:
                raise ValueError("peer evidence symbol mismatch")
        return self

    def row(
        self,
        *,
        price: float,
        market_observed_at: datetime,
        requested_as_of: datetime,
    ) -> PeerMetricRow:
        if price <= 0:
            raise ValueError("peer reference price must be positive")
        if market_observed_at > requested_as_of:
            raise ValueError("peer market timestamp cannot exceed requested_as_of")

        market_cap = price * self.shares_outstanding
        per = price / float(self.eps_yen) if self.eps_yen > 0 else None
        pbr = price / float(self.bps_yen) if self.bps_yen != 0 else None
        revenue_yoy = float(
            self.revenue_million_yen / self.prior_revenue_million_yen
            - Decimal(1)
        )

        free_cash_flow_yield = None
        if (
            self.operating_cash_flow_million_yen is not None
            and self.cash_capex_million_yen is not None
        ):
            fcf_yen = (
                self.operating_cash_flow_million_yen
                - self.cash_capex_million_yen
            ) * Decimal(1_000_000)
            free_cash_flow_yield = float(
                fcf_yen / Decimal(str(market_cap))
            )

        return PeerMetricRow(
            symbol=self.symbol,
            requested_as_of=requested_as_of,
            market_observed_at=market_observed_at,
            market_cap=market_cap,
            price=price,
            per=per,
            pbr=pbr,
            roe=float(self.roe),
            operating_margin=float(self.operating_margin),
            free_cash_flow_yield=free_cash_flow_yield,
            revenue_yoy=revenue_yoy,
        )


def honda_7267_reference() -> AutomotivePeerReference:
    return AutomotivePeerReference(
        symbol="7267",
        company_name="Honda Motor Co., Ltd.",
        issuer_fiscal_label="FYE March 31, 2026",
        period_end=date(2026, 3, 31),
        accounting_standard="IFRS",
        published_at=datetime(2026, 5, 14, 0, 0, tzinfo=JST),
        revenue_million_yen=Decimal(21_796_610),
        prior_revenue_million_yen=Decimal(21_688_767),
        operating_income_million_yen=Decimal(-414_346),
        net_income_million_yen=Decimal(-423_941),
        eps_yen=Decimal("-106.06"),
        bps_yen=Decimal("3035.91"),
        roe=Decimal("-0.035"),
        operating_margin=Decimal("-0.019"),
        shares_outstanding=3_892_580_441,
        operating_cash_flow_million_yen=Decimal(1_135_261),
        cash_capex_million_yen=Decimal(897_545),
        evidence=[
            EvidenceItem(
                symbol="7267",
                excerpt=(
                    "Honda FY2026 sales revenue was JPY 21,796,610 million, "
                    "operating loss was JPY 414,346 million, parent-attributable "
                    "loss was JPY 423,941 million, ROE was -3.5%, and operating "
                    "margin was -1.9%."
                ),
                tags=["peer", "earnings", "fy2026", "official_ir"],
                record=SourceRecord(
                    source_id="peer:7267:ir:fy2026-results",
                    source_type="company_ir",
                    title=(
                        "Honda Consolidated Financial Results for the Fiscal "
                        "Year Ended March 31, 2026"
                    ),
                    published_at=datetime(2026, 5, 14, 0, 0, tzinfo=JST),
                    retrieved_at=datetime(2026, 9, 29, 23, 0, tzinfo=JST),
                    url=HONDA_FY2026_RESULTS_URL,
                    metadata={
                        "security_code": "7267",
                        "accounting_standard": "IFRS",
                        "period_end": "2026-03-31",
                    },
                ),
            ),
            EvidenceItem(
                symbol="7267",
                excerpt=(
                    "Honda FY2026 cash additions were JPY 612,065 million "
                    "for property, plant and equipment and JPY 285,480 million "
                    "for intangible assets."
                ),
                tags=["peer", "cash_flow", "capex", "official_ir"],
                record=SourceRecord(
                    source_id="peer:7267:ir:fy2026-cashflow-reference",
                    source_type="company_ir",
                    title="Honda FY2026 Consolidated Cash Flow",
                    published_at=datetime(2026, 5, 14, 0, 0, tzinfo=JST),
                    retrieved_at=datetime(2026, 9, 29, 23, 0, tzinfo=JST),
                    url=HONDA_FY2026_RESULTS_URL,
                    metadata={
                        "security_code": "7267",
                        "period_end": "2026-03-31",
                    },
                ),
            ),
        ],
        notes=[
            (
                "Honda cash FCF reference uses consolidated operating cash flow "
                "minus cash additions to PPE and intangible assets."
            )
        ],
    )


def nissan_7201_reference() -> AutomotivePeerReference:
    return AutomotivePeerReference(
        symbol="7201",
        company_name="Nissan Motor Co., Ltd.",
        issuer_fiscal_label="FY2025",
        period_end=date(2026, 3, 31),
        accounting_standard="J-GAAP",
        published_at=datetime(2026, 5, 13, 0, 0, tzinfo=JST),
        revenue_million_yen=Decimal(12_007_888),
        prior_revenue_million_yen=Decimal(12_633_214),
        operating_income_million_yen=Decimal(58_005),
        net_income_million_yen=Decimal(-533_095),
        eps_yen=Decimal("-152.58"),
        bps_yen=Decimal("1372.56"),
        roe=Decimal("-0.109"),
        operating_margin=Decimal("0.005"),
        shares_outstanding=3_496_382_520,
        operating_cash_flow_million_yen=Decimal(753_687),
        cash_capex_million_yen=None,
        evidence=[
            EvidenceItem(
                symbol="7201",
                excerpt=(
                    "Nissan FY2025, the year ended March 31, 2026, reported "
                    "net sales of JPY 12,007,888 million, operating income of "
                    "JPY 58,005 million, parent-attributable net loss of "
                    "JPY 533,095 million, ROE of -10.9%, and operating margin "
                    "of 0.5%."
                ),
                tags=["peer", "earnings", "fy2025", "official_ir"],
                record=SourceRecord(
                    source_id="peer:7201:ir:fy2025-results",
                    source_type="company_ir",
                    title="Nissan FY2025 Consolidated Financial Results",
                    published_at=datetime(2026, 5, 13, 0, 0, tzinfo=JST),
                    retrieved_at=datetime(2026, 9, 29, 23, 0, tzinfo=JST),
                    url=NISSAN_FY2025_RESULTS_URL,
                    metadata={
                        "security_code": "7201",
                        "accounting_standard": "J-GAAP",
                        "period_end": "2026-03-31",
                    },
                ),
            )
        ],
        notes=[
            (
                "Nissan labels the year ended March 31, 2026 as FY2025; peer "
                "alignment therefore uses period_end rather than issuer label."
            ),
            (
                "Nissan free-cash-flow yield is omitted because its published "
                "automobile-business FCF is not directly comparable with the "
                "consolidated cash-FCF definition used in this peer table."
            ),
        ],
    )


def toyota_honda_nissan_peer_comparison(
    toyota: ToyotaReferenceAnalysis,
    *,
    honda_price: float,
    nissan_price: float,
) -> tuple[PeerComparisonSet, list[EvidenceItem]]:
    case_as_of = toyota_reference_analysis_context(
        toyota.market
    ).requested_as_of
    observed_at = toyota.market.observed_at

    revenue_trend = toyota.trends.get(CanonicalMetric.REVENUE)
    toyota_row = PeerMetricRow(
        symbol="7203",
        requested_as_of=case_as_of,
        market_observed_at=observed_at,
        market_cap=toyota.market.market_cap,
        price=toyota.market.price,
        per=toyota.metrics.per,
        pbr=toyota.metrics.pbr,
        roe=toyota.metrics.roe,
        operating_margin=toyota.metrics.operating_margin,
        free_cash_flow_yield=toyota.metrics.free_cash_flow_yield,
        revenue_yoy=(
            revenue_trend.year_over_year
            if revenue_trend is not None
            else None
        ),
    )

    honda = honda_7267_reference()
    nissan = nissan_7201_reference()

    if honda.period_end != nissan.period_end or honda.period_end != date(2026, 3, 31):
        raise ValueError("automotive peer periods must align to March 31, 2026")

    comparison = PeerComparisonSet(
        subject_symbol="7203",
        requested_as_of=case_as_of,
        rows=[
            toyota_row,
            honda.row(
                price=honda_price,
                market_observed_at=observed_at,
                requested_as_of=case_as_of,
            ),
            nissan.row(
                price=nissan_price,
                market_observed_at=observed_at,
                requested_as_of=case_as_of,
            ),
        ],
        notes=[
            (
                "Toyota, Honda, and Nissan quantitative rows are aligned to the "
                "common period end March 31, 2026; issuer fiscal-year labels differ."
            ),
            (
                "All three market prices in this reference comparison are injected "
                "regression inputs, not frozen claims about historical market prices."
            ),
            (
                "Honda and Nissan report losses for the common annual period; "
                "PER is therefore unavailable rather than represented as a "
                "negative earnings multiple."
            ),
            *honda.notes,
            *nissan.notes,
        ],
    )
    return comparison, [*honda.evidence, *nissan.evidence]


def toyota_automotive_peer_context(
    market: MarketSnapshot,
    *,
    honda_price: float,
    nissan_price: float,
) -> AnalysisContext:
    toyota = analyze_toyota_reference(market)
    comparison, evidence = toyota_honda_nissan_peer_comparison(
        toyota,
        honda_price=honda_price,
        nissan_price=nissan_price,
    )
    return add_peer_comparison_to_context(
        toyota_reference_analysis_context(market),
        comparison,
        evidence_items=evidence,
    )
