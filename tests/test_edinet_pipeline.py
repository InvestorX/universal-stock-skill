from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime

import httpx
import pytest

from universal_stock_skill.analysis import (
    SnapshotBridgeInputs,
    build_financial_snapshot,
    calculate_stock_metrics,
)
from universal_stock_skill.data import (
    CanonicalMetric,
    EDINETCanonicalPipeline,
    EDINETClient,
    EDINETConfig,
    EDINETDocument,
)

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


def build_csv_zip() -> bytes:
    rows = [
        [
            "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "売上高",
            "CurrentYearDuration",
            "当期",
            "連結",
            "期間",
            "JPY",
            "円",
            "48000000000000",
        ],
        [
            "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "売上高",
            "Prior1YearDuration",
            "前期",
            "連結",
            "期間",
            "JPY",
            "円",
            "44000000000000",
        ],
        [
            "jppfs_cor:OperatingIncome",
            "営業利益",
            "CurrentYearDuration",
            "当期",
            "連結",
            "期間",
            "JPY",
            "円",
            "6000000000000",
        ],
        [
            "jppfs_cor:ProfitLossAttributableToOwnersOfParent",
            "親会社株主に帰属する当期純利益",
            "CurrentYearDuration",
            "当期",
            "連結",
            "期間",
            "JPY",
            "円",
            "5000000000000",
        ],
        [
            "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults",
            "1株当たり当期純利益",
            "CurrentYearDuration",
            "当期",
            "連結",
            "期間",
            "JPYPerShare",
            "円",
            "320",
        ],
        [
            "jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults",
            "1株当たり純資産額",
            "CurrentYearInstant",
            "当期",
            "連結",
            "時点",
            "JPYPerShare",
            "円",
            "2400",
        ],
        [
            "jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults",
            "営業活動によるキャッシュ・フロー",
            "CurrentYearDuration",
            "当期",
            "連結",
            "期間",
            "JPY",
            "円",
            "7000000000000",
        ],
    ]

    text_rows = ["\t".join(f'"{value}"' for value in HEADERS)]
    text_rows.extend("\t".join(f'"{value}"' for value in row) for row in rows)
    raw = ("\r\n".join(text_rows) + "\r\n").encode("utf-16-le")

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("XBRL_TO_CSV/jpcrp-demo.csv", raw)
    return output.getvalue()


def transport() -> httpx.MockTransport:
    payload = build_csv_zip()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/documents/S100DEMO"):
            assert request.url.params["type"] == "5"
            return httpx.Response(200, content=payload)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_edinet_csv_to_stock_metrics_pipeline() -> None:
    client = EDINETClient(
        EDINETConfig(api_key="test-key"),
        transport=transport(),
    )
    document = EDINETDocument(
        docID="S100DEMO",
        secCode="72030",
        filerName="Demo Corporation",
        docTypeCode="120",
        submitDateTime="2026-06-20 15:00",
        periodEnd="2026-03-31",
        csvFlag="1",
    )

    canonical = await EDINETCanonicalPipeline(client).load_document(document)
    snapshot = build_financial_snapshot(
        canonical,
        SnapshotBridgeInputs(
            symbol="7203",
            as_of=datetime(2026, 6, 20, 6, 0, tzinfo=UTC),
            price=3000,
            market_cap=40_000_000_000_000,
            average_equity=30_000_000_000_000,
            capital_expenditure=4_000_000_000_000,
        ),
    )
    metrics = calculate_stock_metrics(snapshot)

    assert snapshot.revenue == 48_000_000_000_000
    assert snapshot.operating_income == 6_000_000_000_000
    assert snapshot.net_income == 5_000_000_000_000
    assert metrics.operating_margin == pytest.approx(0.125)
    assert metrics.free_cash_flow == 3_000_000_000_000


@pytest.mark.asyncio
async def test_pipeline_can_build_historical_canonical_series() -> None:
    client = EDINETClient(
        EDINETConfig(api_key="test-key"),
        transport=transport(),
    )
    document = EDINETDocument(
        docID="S100DEMO",
        secCode="72030",
        filerName="Demo Corporation",
        docTypeCode="120",
        submitDateTime="2026-06-20 15:00",
        periodEnd="2026-03-31",
        csvFlag="1",
    )

    series = await EDINETCanonicalPipeline(client).load_document_series(
        document,
        years=3,
    )

    current = series.get(0)
    prior = series.get(1)

    assert current is not None
    assert prior is not None
    assert current.get(CanonicalMetric.REVENUE).value == 48_000_000_000_000
    assert prior.get(CanonicalMetric.REVENUE).value == 44_000_000_000_000
