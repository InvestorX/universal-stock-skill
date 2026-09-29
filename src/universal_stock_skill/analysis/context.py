from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from universal_stock_skill.analysis.orchestrator import StockAnalysisDataBundle
from universal_stock_skill.analysis.report import EvidenceRef


class AnalysisContext(BaseModel):
    symbol: str = Field(min_length=1)
    requested_as_of: datetime
    evidence: list[EvidenceRef]
    authoritative_facts: dict[str, Any]
    deterministic_metrics: dict[str, float | None]
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
            *self.trends,
            *derivation_ids,
        }


def build_analysis_context(bundle: StockAnalysisDataBundle) -> AnalysisContext:
    filing_source_id = f"edinet:{bundle.filing.selected_doc_id}"
    market_source_id = (
        f"market:{bundle.market.source}:{bundle.market.observed_at.isoformat()}"
    )

    evidence = [
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

    snapshot = bundle.assembly.snapshot
    authoritative_facts: dict[str, Any] = {
        "filing": bundle.filing.model_dump(mode="json"),
        "market": bundle.market.model_dump(mode="json"),
        "financial_snapshot": snapshot.model_dump(mode="json"),
        "mapping_quality": bundle.mapping_quality.model_dump(mode="json"),
        "snapshot_readiness": bundle.snapshot_readiness.model_dump(mode="json"),
    }

    deterministic_metrics = {
        f"metric:{key}": value
        for key, value in bundle.metrics.model_dump(mode="json").items()
    }

    trends = {
        f"trend:{trend.metric.value}": trend.model_dump(mode="json")
        for trend in bundle.trends.trends
    }

    derivations = bundle.assembly.derived.model_dump(mode="json")

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

    limitations.append(
        "This deterministic bundle contains filing and market data only; "
        "it does not contain peer, news, management-guidance, or catalyst evidence."
    )

    return AnalysisContext(
        symbol=bundle.symbol,
        requested_as_of=bundle.requested_as_of,
        evidence=evidence,
        authoritative_facts=authoritative_facts,
        deterministic_metrics=deterministic_metrics,
        trends=trends,
        derivations=derivations,
        limitations=limitations,
    )
