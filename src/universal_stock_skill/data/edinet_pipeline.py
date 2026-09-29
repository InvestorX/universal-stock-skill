from __future__ import annotations

from dataclasses import dataclass, field

from universal_stock_skill.data.canonical import (
    CanonicalFinancialMapper,
    CanonicalFinancialSet,
)
from universal_stock_skill.data.canonical_mappings import DEFAULT_CANONICAL_MAPPER
from universal_stock_skill.data.edinet import EDINETClient, EDINETDocument
from universal_stock_skill.data.edinet_csv import EDINETCsvArchive


class EDINETPipelineError(ValueError):
    pass


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
        if document.csv_flag not in {None, "1"}:
            raise EDINETPipelineError(
                f"document {document.doc_id} does not advertise CSV availability"
            )

        payload = await self.client.download_document(
            document.doc_id,
            document_type=5,
        )
        facts = self.archive_parser.parse(payload)
        return self.mapper.resolve(facts)
