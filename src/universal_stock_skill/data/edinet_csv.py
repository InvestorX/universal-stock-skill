from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, Field


class EDINETCsvFact(BaseModel):
    """One fact from an EDINET XBRL-to-CSV conversion file."""

    element_id: str = Field(alias="要素ID")
    item_name: str = Field(alias="項目名")
    context_id: str = Field(alias="コンテキストID")
    relative_year: str = Field(alias="相対年度")
    consolidation: str = Field(alias="連結・個別")
    period_type: str = Field(alias="期間・時点")
    unit_id: str = Field(alias="ユニットID")
    unit: str = Field(alias="単位")
    raw_value: str = Field(alias="値")
    source_file: str
    row_number: int

    model_config = {"populate_by_name": True}

    @property
    def numeric_value(self) -> Decimal | None:
        """Return a numeric value when the EDINET fact is numeric.

        EDINET documents that a literal "-" in the value column represents
        an explicit zero. Empty strings and textual facts remain None.
        """

        value = self.raw_value.strip()
        if value == "-":
            return Decimal(0)
        if not value:
            return None

        normalized = value.replace(",", "")
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None


@dataclass(frozen=True)
class EDINETCsvArchiveConfig:
    max_files: int = 200
    max_uncompressed_bytes: int = 256 * 1024 * 1024


class EDINETCsvArchiveError(ValueError):
    pass


class EDINETCsvArchive:
    REQUIRED_COLUMNS = {
        "要素ID",
        "項目名",
        "コンテキストID",
        "相対年度",
        "連結・個別",
        "期間・時点",
        "ユニットID",
        "単位",
        "値",
    }

    def __init__(self, config: EDINETCsvArchiveConfig | None = None) -> None:
        self.config = config or EDINETCsvArchiveConfig()

    def parse(self, payload: bytes) -> list[EDINETCsvFact]:
        try:
            archive = zipfile.ZipFile(io.BytesIO(payload))
        except zipfile.BadZipFile as exc:
            raise EDINETCsvArchiveError("EDINET CSV payload is not a valid ZIP archive") from exc

        with archive:
            csv_members = [
                info
                for info in archive.infolist()
                if not info.is_dir() and info.filename.lower().endswith(".csv")
            ]

            if len(csv_members) > self.config.max_files:
                raise EDINETCsvArchiveError(
                    f"archive contains {len(csv_members)} CSV files; "
                    f"limit is {self.config.max_files}"
                )

            total_size = sum(info.file_size for info in csv_members)
            if total_size > self.config.max_uncompressed_bytes:
                raise EDINETCsvArchiveError(
                    f"archive expands to {total_size} bytes of CSV data; "
                    f"limit is {self.config.max_uncompressed_bytes}"
                )

            facts: list[EDINETCsvFact] = []
            for info in csv_members:
                with archive.open(info) as stream:
                    raw = stream.read()
                facts.extend(self._parse_csv_file(info.filename, raw))

            return facts

    def _parse_csv_file(self, source_file: str, raw: bytes) -> list[EDINETCsvFact]:
        text = self._decode_utf16le(raw)
        reader = csv.DictReader(io.StringIO(text), delimiter="\t", quotechar='"')

        fieldnames = set(reader.fieldnames or [])
        missing = self.REQUIRED_COLUMNS - fieldnames
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise EDINETCsvArchiveError(
                f"{source_file} is missing required EDINET columns: {missing_text}"
            )

        facts: list[EDINETCsvFact] = []
        for row_number, row in enumerate(reader, start=2):
            payload = {
                key: (value if value is not None else "")
                for key, value in row.items()
                if key is not None
            }
            payload["source_file"] = source_file
            payload["row_number"] = row_number
            facts.append(EDINETCsvFact.model_validate(payload))

        return facts

    @staticmethod
    def _decode_utf16le(raw: bytes) -> str:
        """Decode the EDINET UTF-16LE format while tolerating an optional BOM."""

        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return raw.decode("utf-16")
        return raw.decode("utf-16-le")
