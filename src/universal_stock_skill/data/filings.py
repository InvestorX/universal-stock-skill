from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

from universal_stock_skill.data.edinet import EDINETDocument

ANNUAL_REPORT_DOC_TYPE = "120"
ANNUAL_REPORT_CORRECTION_DOC_TYPE = "130"


class FilingResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedAnnualFiling:
    original: EDINETDocument
    selected: EDINETDocument
    corrections: tuple[EDINETDocument, ...]

    @property
    def is_corrected(self) -> bool:
        return self.selected.doc_id != self.original.doc_id


class AnnualFilingResolver:
    def resolve(
        self,
        documents: Iterable[EDINETDocument],
        *,
        symbol: str,
        as_of: datetime,
    ) -> ResolvedAnnualFiling:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")

        sec_code = normalize_sec_code(symbol)
        eligible = [
            document
            for document in documents
            if document.sec_code == sec_code and document.published_at() <= as_of
        ]

        originals = [
            document
            for document in eligible
            if document.doc_type_code == ANNUAL_REPORT_DOC_TYPE
        ]
        if not originals:
            raise FilingResolutionError(
                f"no annual report found for security code {sec_code} by {as_of.isoformat()}"
            )

        original = max(
            originals,
            key=lambda document: (
                _period_end(document),
                document.published_at(),
                document.doc_id,
            ),
        )

        corrections = _reachable_corrections(original, eligible)
        selected = corrections[-1] if corrections else original

        return ResolvedAnnualFiling(
            original=original,
            selected=selected,
            corrections=tuple(corrections),
        )


def normalize_sec_code(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if len(normalized) == 4 and normalized.isalnum():
        return normalized + "0"
    if len(normalized) == 5 and normalized.isalnum():
        return normalized
    raise ValueError("security code must be 4 or 5 alphanumeric characters")


def _period_end(document: EDINETDocument) -> date:
    if not document.period_end:
        return date.min

    try:
        return date.fromisoformat(document.period_end)
    except ValueError:
        return date.min


def _reachable_corrections(
    original: EDINETDocument,
    eligible: list[EDINETDocument],
) -> list[EDINETDocument]:
    candidates = [
        document
        for document in eligible
        if document.doc_type_code == ANNUAL_REPORT_CORRECTION_DOC_TYPE
    ]

    reachable_ids = {original.doc_id}
    corrections: list[EDINETDocument] = []

    while True:
        newly_reachable = [
            document
            for document in candidates
            if document.doc_id not in reachable_ids
            and document.parent_doc_id in reachable_ids
        ]
        if not newly_reachable:
            break

        newly_reachable.sort(key=lambda item: (item.published_at(), item.doc_id))
        for document in newly_reachable:
            reachable_ids.add(document.doc_id)
            corrections.append(document)

    corrections.sort(key=lambda item: (item.published_at(), item.doc_id))
    return corrections
