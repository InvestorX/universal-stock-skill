from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from universal_stock_skill.benchmark.reference import (
    FinancialReferencePeriod,
    StockReferenceCase,
)
from universal_stock_skill.evidence.collection import EvidenceItem
from universal_stock_skill.evidence.models import SourceRecord


JST = ZoneInfo("Asia/Tokyo")

TOYOTA_FY2026_SUMMARY_URL = (
    "https://global.toyota/pages/global_toyota/ir/"
    "financial-results/2026_4q_summary_en.pdf"
)
TOYOTA_FY2027_1Q_RESULTS_URL = "https://global.toyota/en/ir/financial-results/"
TOYOTA_2026_BUYBACK_URL = (
    "https://global.toyota/pages/global_toyota/ir/stock/share/"
    "commonstock_20260804_en.pdf"
)


def toyota_7203_reference_case() -> StockReferenceCase:
    return StockReferenceCase(
        case_id="toyota-7203-fy2026",
        symbol="7203",
        company_name="Toyota Motor Corporation",
        accounting_standard="IFRS",
        as_of=datetime(2026, 9, 29, 23, 59, tzinfo=JST),
        periods=[
            FinancialReferencePeriod(
                fiscal_year="FY2026",
                period_end=date(2026, 3, 31),
                values_million_yen={
                    "revenue": Decimal(50_684_952),
                    "operating_income": Decimal(3_766_216),
                    "profit_before_tax": Decimal(5_152_996),
                    "net_income": Decimal(3_985_761),
                    "net_income_attributable_to_parent": Decimal(3_848_098),
                    "total_assets": Decimal(105_522_331),
                    "owners_equity": Decimal(39_918_854),
                    "operating_cash_flow": Decimal(5_472_920),
                    "income_tax_expense": Decimal(1_167_234),
                },
                per_share_yen={
                    "eps_basic": Decimal("295.25"),
                    "eps_diluted": Decimal("295.25"),
                    "bps": Decimal("3062.82"),
                },
                ratios={
                    "roe": Decimal("0.101"),
                    "operating_margin": Decimal("0.074"),
                    "owners_equity_ratio": Decimal("0.378"),
                },
            ),
            FinancialReferencePeriod(
                fiscal_year="FY2025",
                period_end=date(2025, 3, 31),
                values_million_yen={
                    "revenue": Decimal(48_036_704),
                    "operating_income": Decimal(4_795_586),
                    "profit_before_tax": Decimal(6_414_590),
                    "net_income": Decimal(4_789_755),
                    "net_income_attributable_to_parent": Decimal(4_765_086),
                    "total_assets": Decimal(93_601_350),
                    "owners_equity": Decimal(35_924_826),
                    "operating_cash_flow": Decimal(3_696_934),
                    "income_tax_expense": Decimal(1_624_835),
                },
                per_share_yen={
                    "eps_basic": Decimal("359.56"),
                    "eps_diluted": Decimal("359.56"),
                    "bps": Decimal("2753.09"),
                },
                ratios={
                    "roe": Decimal("0.136"),
                    "operating_margin": Decimal("0.100"),
                    "owners_equity_ratio": Decimal("0.384"),
                },
            ),
        ],
        qualitative_evidence=[
            _fy2026_results_evidence(),
            _fy2027_1q_evidence(),
            _buyback_evidence(),
        ],
        notes=[
            "Financial statement amounts are stored in million JPY, matching "
            "Toyota's FY2026 financial summary presentation unit.",
            "The FY2026 results source is dated May 8, 2026. The 14:00 JST "
            "timestamp is the official financial-results press-briefing time.",
            "August 4 evidence uses date-level publication precision normalized "
            "to 00:00 JST; this reference case's as_of is much later the same quarter.",
            "Market price is intentionally not frozen in this case; live valuation "
            "continues to come from the point-in-time MarketDataSource.",
        ],
    )


def _fy2026_results_evidence() -> EvidenceItem:
    return EvidenceItem(
        symbol="7203",
        excerpt=(
            "FY2026 sales revenues were JPY 50,684,952 million, operating "
            "income was JPY 3,766,216 million, and net income attributable "
            "to Toyota Motor Corporation was JPY 3,848,098 million."
        ),
        tags=["earnings", "fy2026", "official_ir"],
        record=SourceRecord(
            source_id="toyota:ir:fy2026-results",
            source_type="company_ir",
            title="Toyota Motor Corporation FY2026 Financial Summary",
            published_at=datetime(2026, 5, 8, 14, 0, tzinfo=JST),
            retrieved_at=datetime(2026, 9, 29, 23, 0, tzinfo=JST),
            url=TOYOTA_FY2026_SUMMARY_URL,
            metadata={
                "security_code": "7203",
                "accounting_standard": "IFRS",
                "period_end": "2026-03-31",
            },
        ),
    )


def _fy2027_1q_evidence() -> EvidenceItem:
    return EvidenceItem(
        symbol="7203",
        excerpt=(
            "Toyota published its FY2027 first-quarter financial results on "
            "August 4, 2026."
        ),
        tags=["earnings", "fy2027_q1", "official_ir"],
        record=SourceRecord(
            source_id="toyota:ir:fy2027-q1-results",
            source_type="company_ir",
            title="Toyota Announces FY2027 1Q Financial Results",
            published_at=datetime(2026, 8, 4, 0, 0, tzinfo=JST),
            retrieved_at=datetime(2026, 9, 29, 23, 0, tzinfo=JST),
            url=TOYOTA_FY2027_1Q_RESULTS_URL,
            metadata={
                "security_code": "7203",
                "timestamp_precision": "date",
            },
        ),
    )


def _buyback_evidence() -> EvidenceItem:
    return EvidenceItem(
        symbol="7203",
        excerpt=(
            "Toyota resolved to repurchase up to 500 million shares for up to "
            "JPY 1,000 billion from August 5, 2026 through August 4, 2027, "
            "and to retire 200 million treasury shares."
        ),
        tags=["capital_allocation", "buyback", "catalyst", "official_ir"],
        record=SourceRecord(
            source_id="toyota:ir:2026-buyback",
            source_type="timely_disclosure",
            title=(
                "Notice Concerning the Determination of Matters Relating to "
                "the Repurchase of Shares of our Common Stock and the "
                "Retirement of Treasury Stock"
            ),
            published_at=datetime(2026, 8, 4, 0, 0, tzinfo=JST),
            retrieved_at=datetime(2026, 9, 29, 23, 0, tzinfo=JST),
            url=TOYOTA_2026_BUYBACK_URL,
            metadata={
                "security_code": "7203",
                "maximum_repurchase_shares": 500_000_000,
                "maximum_repurchase_price_jpy": 1_000_000_000_000,
                "treasury_shares_to_retire": 200_000_000,
                "timestamp_precision": "date",
            },
        ),
    )
