from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from universal_stock_skill.data.edinet import EDINETDocument
from universal_stock_skill.data.filing_discovery import AnnualFilingDiscovery
from universal_stock_skill.data.filings import FilingResolutionError


JST = ZoneInfo("Asia/Tokyo")


class FakeEDINETClient:
    def __init__(self, by_date: dict[date, list[EDINETDocument]]) -> None:
        self.by_date = by_date
        self.calls: list[date] = []

    async def list_documents(self, submission_date: date) -> list[EDINETDocument]:
        self.calls.append(submission_date)
        return self.by_date.get(submission_date, [])


def document(
    doc_id: str,
    *,
    doc_type_code: str,
    submitted: str,
    parent_doc_id: str | None = None,
) -> EDINETDocument:
    return EDINETDocument(
        docID=doc_id,
        secCode="72030",
        filerName="Demo Corporation",
        docTypeCode=doc_type_code,
        submitDateTime=submitted,
        periodStart="2025-04-01",
        periodEnd="2026-03-31",
        parentDocID=parent_doc_id,
        csvFlag="1",
    )


@pytest.mark.asyncio
async def test_discovery_scans_back_and_keeps_later_corrections() -> None:
    client = FakeEDINETClient(
        {
            date(2026, 7, 10): [
                document(
                    "CORR2",
                    doc_type_code="130",
                    submitted="2026-07-10 10:00",
                    parent_doc_id="CORR1",
                )
            ],
            date(2026, 7, 1): [
                document(
                    "CORR1",
                    doc_type_code="130",
                    submitted="2026-07-01 10:00",
                    parent_doc_id="BASE",
                )
            ],
            date(2026, 6, 20): [
                document(
                    "BASE",
                    doc_type_code="120",
                    submitted="2026-06-20 15:00",
                )
            ],
        }
    )

    result = await AnnualFilingDiscovery(
        client=client,
        lookback_days=100,
    ).discover(
        symbol="7203",
        as_of=datetime(2026, 7, 20, 12, 0, tzinfo=JST),
    )

    assert result.selected.doc_id == "CORR2"
    assert [item.doc_id for item in result.corrections] == ["CORR1", "CORR2"]
    assert client.calls[-1] == date(2026, 6, 20)


@pytest.mark.asyncio
async def test_same_day_future_filing_does_not_stop_search() -> None:
    client = FakeEDINETClient(
        {
            date(2026, 6, 20): [
                document(
                    "FUTURE",
                    doc_type_code="120",
                    submitted="2026-06-20 15:00",
                )
            ],
            date(2026, 6, 19): [
                document(
                    "VISIBLE",
                    doc_type_code="120",
                    submitted="2026-06-19 15:00",
                )
            ],
        }
    )

    result = await AnnualFilingDiscovery(
        client=client,
        lookback_days=3,
    ).discover(
        symbol="7203",
        as_of=datetime(2026, 6, 20, 12, 0, tzinfo=JST),
    )

    assert result.selected.doc_id == "VISIBLE"


@pytest.mark.asyncio
async def test_discovery_respects_lookback_limit() -> None:
    client = FakeEDINETClient({})

    with pytest.raises(FilingResolutionError):
        await AnnualFilingDiscovery(
            client=client,
            lookback_days=2,
        ).discover(
            symbol="7203",
            as_of=datetime(2026, 6, 20, 12, 0, tzinfo=JST),
        )

    assert len(client.calls) == 3
