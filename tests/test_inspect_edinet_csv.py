import io
import zipfile
from pathlib import Path

import pytest

from scripts.inspect_edinet_csv import build_inspection_payload, main

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


def sample_zip() -> bytes:
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
            "110",
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
            "100",
        ],
    ]

    text_rows = ["\t".join(f'"{value}"' for value in HEADERS)]
    text_rows.extend("\t".join(f'"{value}"' for value in row) for row in rows)
    raw = ("\r\n".join(text_rows) + "\r\n").encode("utf-16-le")

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("XBRL_TO_CSV/jpcrp-demo.csv", raw)
    return output.getvalue()


def test_script_module_is_importable() -> None:
    assert Path(main.__code__.co_filename).name == "inspect_edinet_csv.py"


def test_inspection_payload_contains_current_series_and_trends() -> None:
    result = build_inspection_payload(sample_zip(), years=2)

    assert result["fact_count"] == 2
    current_facts = result["current"]["facts"]
    assert current_facts[0]["metric"] == "revenue"
    assert current_facts[0]["value"] == "110"

    periods = result["series"]["periods"]
    assert [item["year_offset"] for item in periods] == [0, 1]

    revenue = next(
        item
        for item in result["trends"]["trends"]
        if item["metric"] == "revenue"
    )
    assert revenue["year_over_year"] == pytest.approx(0.1)
