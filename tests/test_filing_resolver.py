from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from universal_stock_skill.data.edinet import EDINETDocument
from universal_stock_skill.data.filings import (
    AnnualFilingResolver,
    FilingResolutionError,
    normalize_sec_code,
)

JST = ZoneInfo("Asia/Tokyo")


def document(
    doc_id: str,
    *,
    doc_type_code: str,
    submit_date_time: str,
    period_end: str,
    parent_doc_id: str | None = None,
) -> EDINETDocument:
    return EDINETDocument(
        docID=doc_id,
        secCode="72030",
        filerName="Demo Corporation",
        docTypeCode=doc_type_code,
        submitDateTime=submit_date_time,
        periodEnd=period_end,
        parentDocID=parent_doc_id,
        csvFlag="1",
    )


def test_normalize_security_code() -> None:
    assert normalize_sec_code("7203") == "72030"
    assert normalize_sec_code("72030") == "72030"
    assert normalize_sec_code("A123") == "A1230"


def test_latest_annual_period_is_selected() -> None:
    resolver = AnnualFilingResolver()
    result = resolver.resolve(
        [
            document(
                "OLD",
                doc_type_code="120",
                submit_date_time="2025-06-20 15:00",
                period_end="2025-03-31",
            ),
            document(
                "NEW",
                doc_type_code="120",
                submit_date_time="2026-06-20 15:00",
                period_end="2026-03-31",
            ),
        ],
        symbol="7203",
        as_of=datetime(2026, 9, 1, tzinfo=JST),
    )

    assert result.original.doc_id == "NEW"
    assert result.selected.doc_id == "NEW"
    assert not result.is_corrected


def test_latest_reachable_correction_is_selected() -> None:
    resolver = AnnualFilingResolver()
    result = resolver.resolve(
        [
            document(
                "BASE",
                doc_type_code="120",
                submit_date_time="2026-06-20 15:00",
                period_end="2026-03-31",
            ),
            document(
                "CORR1",
                doc_type_code="130",
                submit_date_time="2026-07-01 10:00",
                period_end="2026-03-31",
                parent_doc_id="BASE",
            ),
            document(
                "CORR2",
                doc_type_code="130",
                submit_date_time="2026-07-10 10:00",
                period_end="2026-03-31",
                parent_doc_id="CORR1",
            ),
        ],
        symbol="7203",
        as_of=datetime(2026, 9, 1, tzinfo=JST),
    )

    assert result.selected.doc_id == "CORR2"
    assert [item.doc_id for item in result.corrections] == ["CORR1", "CORR2"]


def test_future_correction_is_not_visible() -> None:
    resolver = AnnualFilingResolver()
    result = resolver.resolve(
        [
            document(
                "BASE",
                doc_type_code="120",
                submit_date_time="2026-06-20 15:00",
                period_end="2026-03-31",
            ),
            document(
                "CORR",
                doc_type_code="130",
                submit_date_time="2026-10-01 10:00",
                period_end="2026-03-31",
                parent_doc_id="BASE",
            ),
        ],
        symbol="7203",
        as_of=datetime(2026, 9, 1, tzinfo=JST),
    )

    assert result.selected.doc_id == "BASE"


def test_missing_annual_report_is_explicit() -> None:
    with pytest.raises(FilingResolutionError):
        AnnualFilingResolver().resolve(
            [],
            symbol="7203",
            as_of=datetime(2026, 9, 1, tzinfo=JST),
        )
