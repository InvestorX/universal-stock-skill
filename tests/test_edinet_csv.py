from __future__ import annotations

import io
import zipfile
from decimal import Decimal

import pytest

from universal_stock_skill.data.edinet_csv import (
    EDINETCsvArchive,
    EDINETCsvArchiveError,
)
from universal_stock_skill.data.facts import FactQuery, FactSet

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


def archive_with_tsv(rows: list[list[str]]) -> bytes:
    text_rows = ["\t".join(f'"{value}"' for value in HEADERS)]
    text_rows.extend("\t".join(f'"{value}"' for value in row) for row in rows)
    raw = ("\r\n".join(text_rows) + "\r\n").encode("utf-16-le")

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("XBRL_TO_CSV/jpcrp-test.csv", raw)
    return output.getvalue()


def test_parse_official_nine_column_format() -> None:
    payload = archive_with_tsv(
        [
            [
                "jppfs_cor:NetSales",
                "売上高",
                "CurrentYearDuration",
                "当期",
                "連結",
                "期間",
                "JPY",
                "円",
                "123456",
            ]
        ]
    )

    facts = EDINETCsvArchive().parse(payload)

    assert len(facts) == 1
    assert facts[0].element_id == "jppfs_cor:NetSales"
    assert facts[0].numeric_value == Decimal(123456)
    assert facts[0].source_file.endswith("jpcrp-test.csv")
    assert facts[0].row_number == 2


def test_dash_is_explicit_zero_and_text_is_not_numeric() -> None:
    payload = archive_with_tsv(
        [
            ["a", "A", "ctx", "当期", "連結", "期間", "JPY", "円", "-"],
            ["b", "B", "ctx", "当期", "その他", "期間", "-", "-", "説明テキスト"],
        ]
    )

    facts = EDINETCsvArchive().parse(payload)
    assert facts[0].numeric_value == Decimal(0)
    assert facts[1].numeric_value is None


def test_fact_set_requires_unambiguous_numeric_match() -> None:
    payload = archive_with_tsv(
        [
            [
                "jppfs_cor:NetSales",
                "売上高",
                "CurrentYearDuration",
                "当期",
                "連結",
                "期間",
                "JPY",
                "円",
                "100",
            ],
            [
                "jppfs_cor:NetSales",
                "売上高",
                "Prior1YearDuration",
                "前期",
                "連結",
                "期間",
                "JPY",
                "円",
                "90",
            ],
        ]
    )
    facts = EDINETCsvArchive().parse(payload)
    fact_set = FactSet(facts)

    value = fact_set.unique_numeric(
        FactQuery(
            element_ids=frozenset({"jppfs_cor:NetSales"}),
            context_ids=frozenset({"CurrentYearDuration"}),
        )
    )
    assert value == Decimal(100)

    with pytest.raises(LookupError):
        fact_set.unique_numeric(
            FactQuery(element_ids=frozenset({"jppfs_cor:NetSales"}))
        )


def test_invalid_zip_is_rejected() -> None:
    with pytest.raises(EDINETCsvArchiveError):
        EDINETCsvArchive().parse(b"not-a-zip")
