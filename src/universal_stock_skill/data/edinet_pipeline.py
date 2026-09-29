from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel

from universal_stock_skill.data.canonical import (
    CanonicalFinancialMapper,
    CanonicalFinancialSeries,
    CanonicalFinancialSet,
)
from universal_stock_skill.data.canonical_mappings import DEFAULT_CANONICAL_MAPPER
from universal_stock_skill.data.edinet import EDINETClient, EDINETDocument
from universal_stock_skill.data.edinet_csv import EDINETCsvArchive, EDINETCsvFact


class EDINETPipelineError(ValueError):
    pass


class EDINETCanonicalBundle(BaseModel):
    current: CanonicalFinancialSet
    series: CanonicalFinancialSeries


@dataclass
class EDINETCanonicalPipeline:
    client: EDINETClient
    mapper: CanonicalFinancialMapper = field(
        default_factory=lambda: DEFAULT_CANONICAL_MAPPER
    )
    archive_parser: EDINETCsvArchive = field(default_factory=EDINETCsvArchive)

    async def load_document(
        self,
        document: EDINETDocument,
    ) -> CanonicalFinancialSet:
        facts = await self._load_facts(document)
        return self.mapper.resolve(facts)

    async def load_document_series(
        self,
        document: EDINETDocument,
        *,
        years: int = 5,
    ) -> CanonicalFinancialSeries:
        facts = await self._load_facts(document)
        return self.mapper.resolve_series(facts, years=years)

    async def load_document_bundle(
        self,
        document: EDINETDocument,
        *,
        years: int = 5,
    ) -> EDINETCanonicalBundle:
        facts = await self._load_facts(document)
        return EDINETCanonicalBundle(
            current=self.mapper.resolve(facts),
            series=self.mapper.resolve_series(facts, years=years),
        )

    async def _load_facts(
        self,
        document: EDINETDocument,
    ) -> list[EDINETCsvFact]:
        if document.csv_flag not in {None, "1"}:
            raise EDINETPipelineError(
                f"document {document.doc_id} does not advertise CSV availability"
            )

        payload = await self.client.download_document(
            document.doc_id,
            document_type=5,
        )
        return self.archive_parser.parse(payload)
