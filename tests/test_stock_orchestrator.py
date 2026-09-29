from __future__ import annotations

import io
import zipfile
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from universal_stock_skill.analysis.orchestrator import StockAnalysisOrchestrator
from universal_stock_skill.data.canonical import CanonicalMetric
from universal_stock_skill.data.edinet import EDINETDocument
from universal_stock_skill.data.edinet_pipeline import EDINETCanonicalPipeline
from universal_stock_skill.data.filing_discovery import AnnualFilingDiscovery
from universal_stock_skill.data.market import MarketSnapshot


JST = ZoneInfo("Asia/Tokyo")

HEADERS = [
    "要素ID",
    "項目名",
    "コンテキストID",
    "相対年度",
    "連結・個別",
    "期間・時点",
    "ユニットID",
    "単位",
    "値",
]


def edinet_zip() -> bytes:
    rows = [
        ["jpcrp_cor:NetSalesSummaryOfBusinessResults", "売上高", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "1100"],
        ["jpcrp_cor:NetSalesSummaryOfBusinessResults", "売上高", "Prior1YearDuration", "前期", "連結", "期間", "JPY", "円", "1000"],
        ["jppfs_cor:OperatingIncome", "営業利益", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "120"],
        ["jppfs_cor:IncomeBeforeIncomeTaxes", "税引前利益", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "100"],
        ["jppfs_cor:IncomeTaxes", "法人税等", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "30"],
        ["jppfs_cor:ProfitLossAttributableToOwnersOfParent", "親会社株主に帰属する当期純利益", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "70"],
        ["jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults", "EPS", "CurrentYearDuration", "当期", "連結", "期間", "JPYPerShare", "円", "10"],
        ["jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults", "BPS", "CurrentYearInstant", "当期", "連結", "時点", "JPYPerShare", "円", "100"],
        ["jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults", "ROE", "CurrentYearDuration", "当期", "連結", "期間", "pure", "pure", "0.10"],
        ["jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults", "営業CF", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "150"],
        ["jppfs_cor:PurchaseOfPropertyPlantAndEquipmentInvCF", "有形固定資産取得", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "-40"],
        ["jppfs_cor:PurchaseOfIntangibleAssetsInvCF", "無形固定資産取得", "CurrentYearDuration", "当期", "連結", "期間", "JPY", "円", "-10"],
    ]

    text_rows = ["\t".join(f'"{value}"' for value in HEADERS)]
    text_rows.extend("\t".join(f'"{value}"' for value in row) for row in rows)
    raw = ("\r\n".join(text_rows) + "\r\n").encode("utf-16-le")

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("XBRL_TO_CSV/jpcrp-demo.csv", raw)
    return output.getvalue()


class FakeEDINETClient:
    def __init__(self) -> None:
        self.payload = edinet_zip()

    async def list_documents(self, submission_date: date) -> list[EDINETDocument]:
        if submission_date == date(2026, 7, 1):
            return [
                EDINETDocument(
                    docID="CORR",
                    secCode="72030",
                    filerName="Demo Corporation",
                    docTypeCode="130",
                    submitDateTime="2026-07-01 10:00",
                    periodStart="2025-04-01",
                    periodEnd="2026-03-31",
                    parentDocID="BASE",
                    csvFlag="1",
                )
            ]
        if submission_date == date(2026, 6, 20):
            return [
                EDINETDocument(
                    docID="BASE",
                    secCode="72030",
                    filerName="Demo Corporation",
                    docTypeCode="120",
                    submitDateTime="2026-06-20 15:00",
                    periodStart="2025-04-01",
                    periodEnd="2026-03-31",
                    csvFlag="1",
                )
            ]
        return []

    async def download_document(
        self,
        doc_id: str,
        *,
        document_type: int = 1,
    ) -> bytes:
        assert doc_id == "CORR"
        assert document_type == 5
        return self.payload


class FakeMarketSource:
    async def get_market_snapshot(
        self,
        symbol: str,
        as_of: datetime,
    ) -> MarketSnapshot:
        assert symbol == "7203"
        assert as_of == datetime(2026, 9, 29, 23, 0, tzinfo=JST)
        return MarketSnapshot(
            symbol=symbol,
            observed_at=datetime(2026, 9, 29, 6, 30, tzinfo=UTC),
            price=120,
            currency="JPY",
            source="fixture",
            market_cap=12_000,
        )


@pytest.mark.asyncio
async def test_stock_orchestrator_runs_end_to_end_without_llm() -> None:
    edinet = FakeEDINETClient()
    orchestrator = StockAnalysisOrchestrator(
        filing_discovery=AnnualFilingDiscovery(
            client=edinet,
            lookback_days=120,
        ),
        edinet_pipeline=EDINETCanonicalPipeline(client=edinet),
        market_source=FakeMarketSource(),
    )

    result = await orchestrator.analyze(
        "7203",
        as_of=datetime(2026, 9, 29, 23, 0, tzinfo=JST),
        years=2,
    )

    assert result.filing.original_doc_id == "BASE"
    assert result.filing.selected_doc_id == "CORR"
    assert result.filing.correction_doc_ids == ["CORR"]
    assert result.mapping_quality.coverage_ratio > 0
    assert result.snapshot_readiness.ready

    revenue_trend = result.trends.get(CanonicalMetric.REVENUE)
    assert revenue_trend is not None
    assert revenue_trend.year_over_year == pytest.approx(0.10)

    snapshot = result.assembly.snapshot
    assert snapshot.price == 120
    assert snapshot.average_equity == 700
    assert snapshot.capital_expenditure == 50
    assert snapshot.nopat == pytest.approx(84)

    assert result.metrics.per == pytest.approx(12)
    assert result.metrics.pbr == pytest.approx(1.2)
    assert result.metrics.roe == pytest.approx(0.1)
    assert result.metrics.free_cash_flow == pytest.approx(100)
    assert result.metrics.free_cash_flow_yield == pytest.approx(100 / 12_000)
    assert result.metrics.roic is None

    payload = result.model_dump(mode="json")
    assert payload["filing"]["selected_doc_id"] == "CORR"
    assert payload["assembly"]["derived"]["average_equity_method"] == "official_roe_backsolve"
