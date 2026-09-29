from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel

from universal_stock_skill.analysis.context import AnalysisContext, build_analysis_context
from universal_stock_skill.analysis.orchestrator import (
    StockAnalysisDataBundle,
    StockAnalysisOrchestrator,
)
from universal_stock_skill.analysis.peers import (
    PeerComparisonError,
    PeerComparisonSet,
    build_peer_comparison,
)
from universal_stock_skill.evidence.collection import EvidenceItem


class PeerAnalysisResult(BaseModel):
    subject: StockAnalysisDataBundle
    peers: list[StockAnalysisDataBundle]
    comparison: PeerComparisonSet

    def build_context(self, *, evidence_items: Sequence[EvidenceItem] = ()) -> AnalysisContext:
        return build_analysis_context(
            self.subject,
            evidence_items=evidence_items,
            peer_bundles=self.peers,
        )


class PeerAnalysisOrchestrator:
    def __init__(self, stock_orchestrator: StockAnalysisOrchestrator) -> None:
        self._stock_orchestrator = stock_orchestrator

    async def analyze(
        self,
        subject_symbol: str,
        *,
        peer_symbols: Sequence[str],
        as_of: datetime,
        years: int = 5,
    ) -> PeerAnalysisResult:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if not peer_symbols:
            raise PeerComparisonError("at least one peer symbol is required")

        symbols = [
            _normalize_symbol(subject_symbol),
            *[_normalize_symbol(symbol) for symbol in peer_symbols],
        ]
        if len(symbols) != len(set(symbols)):
            raise PeerComparisonError("peer symbols must be unique")

        bundles = await asyncio.gather(
            *[
                self._stock_orchestrator.analyze(symbol, as_of=as_of, years=years)
                for symbol in symbols
            ]
        )
        subject, *peers = bundles
        return PeerAnalysisResult(
            subject=subject,
            peers=peers,
            comparison=build_peer_comparison(subject, peers),
        )


def _normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized:
        raise PeerComparisonError("peer symbols must not be blank")
    return normalized
