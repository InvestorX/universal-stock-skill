from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from universal_stock_skill.analysis.orchestrator import StockAnalysisDataBundle
from universal_stock_skill.analysis.peers import (
    PeerComparisonSet,
    build_peer_comparison,
)
from universal_stock_skill.analysis.report import EvidenceRef
from universal_stock_skill.evidence.collection import EvidenceItem


class AnalysisContext(BaseModel):
    symbol: str = Field(min_length=1)
    requested_as_of: datetime
    evidence: list[EvidenceRef]
    authoritative_facts: dict[str, Any]
    deterministic_metrics: dict[str, float | None]
    peer_metrics: dict[str, float | None] = Field(default_factory=dict)
    trends: dict[str, dict[str, Any]]
    derivations: dict[str, Any]
    limitations: list[str]

    @model_validator(mode="after")
    def validate_point_in_time(self) -> AnalysisContext:
        if (
            self.requested_as_of.tzinfo is None
            or self.requested_as_of.utcoffset() is None
        ):
            raise ValueError("requested_as_of must be timezone-aware")

        source_ids = [item.source_id for item in self.evidence]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("evidence source_id values must be unique")

        for item in self.evidence:
            if item.published_at is None:
                continue
            if (
                item.published_at.tzinfo is None
                or item.published_at.utcoffset() is None
            ):
                raise ValueError(
                    f"evidence {item.source_id} published_at must be timezone-aware"
                )
            if item.published_at > self.requested_as_of:
                raise ValueError(
                    f"evidence {item.source_id} is newer than requested_as_of"
                )

        return self

    @property
    def evidence_ids(self) -> set[str]:
        return {item.source_id for item in self.evidence}

    @property
    def metric_ids(self) -> set[str]:
        derivation_ids = {
            f"derivation:{key}"
            for key, value in self.derivations.items()
            if value is not None and not key.endswith("_method")
        }
        return {
            *self.deterministic_metrics,
            *self.peer_metrics,
            *self.trends,
            *derivation_ids,
        }


def build_analysis_context(
    bundle: StockAnalysisDataBundle,
    *,
    evidence_items: Sequence[EvidenceItem] = (),
    peer_bundles: Sequence[StockAnalysisDataBundle] = (),
) -> AnalysisContext:
    evidence = _bundle_evidence_refs(bundle)

    for item in evidence_items:
        evidence.append(
            EvidenceRef(
                source_id=item.record.source_id,
                title=item.record.title,
                url=item.record.url,
                published_at=item.record.published_at,
            )
        )

    peer_metrics: dict[str, float | None] = {}
    peer_comparison = None
    if peer_bundles:
        peer_comparison = build_peer_comparison(
            bundle,
            list(peer_bundles),
        )
        peer_metrics = peer_comparison.metric_values()
        for peer in peer_bundles:
            evidence.extend(
                _bundle_evidence_refs(
                    peer,
                    prefix=f"peer:{peer.symbol.strip().upper()}:",
                )
            )

    snapshot = bundle.assembly.snapshot
    authoritative_facts: dict[str, Any] = {
        "filing": bundle.filing.model_dump(mode="json"),
        "market": bundle.market.model_dump(mode="json"),
        "financial_snapshot": snapshot.model_dump(mode="json"),
        "mapping_quality": bundle.mapping_quality.model_dump(mode="json"),
        "snapshot_readiness": bundle.snapshot_readiness.model_dump(mode="json"),
    }

    if evidence_items:
        authoritative_facts["qualitative_evidence"] = [
            item.model_dump(mode="json")
            for item in evidence_items
        ]

    if peer_comparison is not None:
        authoritative_facts["peer_comparison"] = peer_comparison.model_dump(
            mode="json"
        )

    deterministic_metrics = {
        f"metric:{key}": value
        for key, value in bundle.metrics.model_dump(mode="json").items()
    }

    trends = {
        f"trend:{trend.metric.value}": trend.model_dump(mode="json")
        for trend in bundle.trends.trends
    }

    derivations = bundle.assembly.derived.model_dump(mode="json")
    limitations = _build_limitations(
        bundle,
        evidence_items=evidence_items,
        peer_bundles=peer_bundles,
    )

    return AnalysisContext(
        symbol=bundle.symbol,
        requested_as_of=bundle.requested_as_of,
        evidence=evidence,
        authoritative_facts=authoritative_facts,
        deterministic_metrics=deterministic_metrics,
        peer_metrics=peer_metrics,
        trends=trends,
        derivations=derivations,
        limitations=limitations,
    )


def _bundle_evidence_refs(
    bundle: StockAnalysisDataBundle,
    *,
    prefix: str = "",
) -> list[EvidenceRef]:
    filing_source_id = f"{prefix}edinet:{bundle.filing.selected_doc_id}"
    market_source_id = (
        f"{prefix}market:{bundle.market.source}:"
        f"{bundle.market.observed_at.isoformat()}"
    )

    return [
        EvidenceRef(
            source_id=filing_source_id,
            title=(
                f"{bundle.filing.filer_name or bundle.symbol} "
                f"annual filing {bundle.filing.selected_doc_id}"
            ),
            published_at=bundle.filing.published_at,
        ),
        EvidenceRef(
            source_id=market_source_id,
            title=(
                f"{bundle.symbol} market snapshot "
                f"({bundle.market.source}, {bundle.market.observed_at.isoformat()})"
            ),
            published_at=bundle.market.observed_at,
        ),
    ]


def _build_limitations(
    bundle: StockAnalysisDataBundle,
    *,
    evidence_items: Sequence[EvidenceItem],
    peer_bundles: Sequence[StockAnalysisDataBundle],
) -> list[str]:
    limitations: list[str] = []

    if bundle.mapping_quality.missing_metrics:
        limitations.append(
            "Canonical mapping is missing metrics: "
            + ", ".join(
                metric.value
                for metric in bundle.mapping_quality.missing_metrics
            )
        )

    if bundle.mapping_quality.fallback_metrics:
        limitations.append(
            "Extension fallback was used for metrics: "
            + ", ".join(
                metric.value
                for metric in bundle.mapping_quality.fallback_metrics
            )
        )

    if bundle.metrics.roic is None:
        limitations.append(
            "ROIC is unavailable because average invested capital is not "
            "derived automatically yet."
        )

    source_types = {
        item.record.source_type
        for item in evidence_items
    }

    if not peer_bundles:
        limitations.append("Deterministic peer comparison data is unavailable.")
    if "news" not in source_types:
        limitations.append("News evidence is unavailable.")
    if "company_ir" not in source_types:
        limitations.append("Company IR / management-guidance evidence is unavailable.")
    if not {"timely_disclosure", "company_ir"} & source_types:
        limitations.append("Timely-disclosure / catalyst evidence is unavailable.")

    return limitations



def add_peer_comparison_to_context(
    context: AnalysisContext,
    comparison: PeerComparisonSet,
    *,
    evidence_items: Sequence[EvidenceItem] = (),
) -> AnalysisContext:
    if comparison.subject_symbol.strip().upper() != context.symbol.strip().upper():
        raise ValueError("peer comparison subject does not match analysis context")
    if comparison.requested_as_of != context.requested_as_of:
        raise ValueError("peer comparison requested_as_of must match analysis context")

    evidence = list(context.evidence)
    for item in evidence_items:
        evidence.append(
            EvidenceRef(
                source_id=item.record.source_id,
                title=item.record.title,
                url=item.record.url,
                published_at=item.record.published_at,
            )
        )

    authoritative_facts = dict(context.authoritative_facts)
    authoritative_facts["peer_comparison"] = comparison.model_dump(mode="json")
    if evidence_items:
        authoritative_facts["peer_evidence"] = [
            item.model_dump(mode="json")
            for item in evidence_items
        ]

    limitations = [
        item
        for item in context.limitations
        if item != "Deterministic peer comparison data is unavailable."
    ]
    limitations.extend(
        note
        for note in comparison.notes
        if note not in limitations
    )

    return AnalysisContext(
        symbol=context.symbol,
        requested_as_of=context.requested_as_of,
        evidence=evidence,
        authoritative_facts=authoritative_facts,
        deterministic_metrics=dict(context.deterministic_metrics),
        peer_metrics=comparison.metric_values(),
        trends=dict(context.trends),
        derivations=dict(context.derivations),
        limitations=limitations,
    )
