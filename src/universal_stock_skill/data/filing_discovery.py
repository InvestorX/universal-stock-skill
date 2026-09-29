from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from universal_stock_skill.data.edinet import EDINETClient, EDINETDocument
from universal_stock_skill.data.filings import (
    ANNUAL_REPORT_CORRECTION_DOC_TYPE,
    ANNUAL_REPORT_DOC_TYPE,
    AnnualFilingResolver,
    FilingResolutionError,
    ResolvedAnnualFiling,
    normalize_sec_code,
)


@dataclass
class AnnualFilingDiscovery:
    client: EDINETClient
    resolver: AnnualFilingResolver = AnnualFilingResolver()
    lookback_days: int = 550

    async def discover(
        self,
        *,
        symbol: str,
        as_of: datetime,
    ) -> ResolvedAnnualFiling:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if self.lookback_days < 1:
            raise ValueError("lookback_days must be >= 1")

        sec_code = normalize_sec_code(symbol)
        collected: list[EDINETDocument] = []

        for offset in range(self.lookback_days + 1):
            submission_date = as_of.date() - timedelta(days=offset)
            documents = await self.client.list_documents(submission_date)
            matching = [
                document
                for document in documents
                if document.sec_code == sec_code
                and document.doc_type_code
                in {
                    ANNUAL_REPORT_DOC_TYPE,
                    ANNUAL_REPORT_CORRECTION_DOC_TYPE,
                }
            ]
            collected.extend(matching)

            if any(
                document.doc_type_code == ANNUAL_REPORT_DOC_TYPE
                and document.published_at() <= as_of
                for document in matching
            ):
                return self.resolver.resolve(
                    collected,
                    symbol=symbol,
                    as_of=as_of,
                )

        raise FilingResolutionError(
            f"no annual report found for {sec_code} within "
            f"{self.lookback_days} days before {as_of.isoformat()}"
        )
