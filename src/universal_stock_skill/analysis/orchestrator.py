from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from universal_stock_skill.analysis.assembly import (
    FinancialSnapshotAssemblyResult,
    assemble_financial_snapshot,
)
from universal_stock_skill.analysis.bridge import (
    SnapshotCanonicalReadiness,
    evaluate_snapshot_readiness,
)
from universal_stock_skill.analysis.models import StockMetrics
from universal_stock_skill.analysis.trends import (
    CanonicalTrendSet,
    calculate_canonical_trends,
)
from universal_stock_skill.analysis.workflow import calculate_stock_metrics
from universal_stock_skill.data.canonical import CanonicalMetric
from universal_stock_skill.data.canonical_quality import (
    CanonicalMappingQuality,
    evaluate_mapping_quality,
)
from universal_stock_skill.data.edinet_pipeline import EDINETCanonicalPipeline
from universal_stock_skill.data.filing_discovery import AnnualFilingDiscovery
from universal_stock_skill.data.market import MarketDataSource, MarketSnapshot

DEFAULT_TREND_METRICS = [
    CanonicalMetric.REVENUE,
    CanonicalMetric.OPERATING_INCOME,
    CanonicalMetric.NET_INCOME,
    CanonicalMetric.EPS,
    CanonicalMetric.CF_OPERATING,
]


class FilingSelectionSummary(BaseModel):
    original_doc_id: str
    selected_doc_id: str
    correction_doc_ids: list[str]
    is_corrected: bool
    filer_name: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    published_at: datetime


class StockAnalysisDataBundle(BaseModel):
    symbol: str = Field(min_length=1)
    requested_as_of: datetime
    filing: FilingSelectionSummary
    market: MarketSnapshot
    mapping_quality: CanonicalMappingQuality
    snapshot_readiness: SnapshotCanonicalReadiness
    trends: CanonicalTrendSet
    assembly: FinancialSnapshotAssemblyResult
    metrics: StockMetrics

    @field_validator("requested_as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("requested_as_of must be timezone-aware")
        return value


class StockAnalysisOrchestrator:
    def __init__(
        self,
        *,
        filing_discovery: AnnualFilingDiscovery,
        edinet_pipeline: EDINETCanonicalPipeline,
        market_source: MarketDataSource,
    ) -> None:
        self._filing_discovery = filing_discovery
        self._edinet_pipeline = edinet_pipeline
        self._market_source = market_source

    async def analyze(
        self,
        symbol: str,
        *,
        as_of: datetime,
        years: int = 5,
    ) -> StockAnalysisDataBundle:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")

        filing = await self._filing_discovery.discover(
            symbol=symbol,
            as_of=as_of,
        )
        canonical = await self._edinet_pipeline.load_document_bundle(
            filing.selected,
            years=years,
        )
        market = await self._market_source.get_market_snapshot(
            symbol,
            as_of,
        )

        quality = evaluate_mapping_quality(canonical.current)
        readiness = evaluate_snapshot_readiness(canonical.current)
        trends = calculate_canonical_trends(
            canonical.series,
            DEFAULT_TREND_METRICS,
        )
        assembly = assemble_financial_snapshot(
            canonical.current,
            canonical.series,
            market,
        )
        metrics = calculate_stock_metrics(assembly.snapshot)

        return StockAnalysisDataBundle(
            symbol=symbol.strip().upper(),
            requested_as_of=as_of,
            filing=FilingSelectionSummary(
                original_doc_id=filing.original.doc_id,
                selected_doc_id=filing.selected.doc_id,
                correction_doc_ids=[
                    document.doc_id
                    for document in filing.corrections
                ],
                is_corrected=filing.is_corrected,
                filer_name=filing.selected.filer_name,
                period_start=filing.selected.period_start,
                period_end=filing.selected.period_end,
                published_at=filing.selected.published_at(),
            ),
            market=market,
            mapping_quality=quality,
            snapshot_readiness=readiness,
            trends=trends,
            assembly=assembly,
            metrics=metrics,
        )
