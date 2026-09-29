from __future__ import annotations

from universal_stock_skill.analysis.context import AnalysisContext
from universal_stock_skill.analysis.report import (
    ClaimKind,
    EvidenceRef,
    StockAnalysisReport,
)


class ReportGroundingError(ValueError):
    pass


def ground_report(
    report: StockAnalysisReport,
    context: AnalysisContext,
) -> StockAnalysisReport:
    if not report.claims:
        raise ReportGroundingError(
            "grounded analysis report must contain at least one structured claim"
        )

    known_evidence = {
        item.source_id: item
        for item in context.evidence
    }
    known_metrics = context.metric_ids
    referenced_evidence: set[str] = set()

    for claim in report.claims:
        unknown_evidence = set(claim.evidence_ids) - set(known_evidence)
        if unknown_evidence:
            raise ReportGroundingError(
                "claim references unknown evidence: "
                + ", ".join(sorted(unknown_evidence))
            )

        unknown_metrics = set(claim.metric_ids) - known_metrics
        if unknown_metrics:
            raise ReportGroundingError(
                "claim references unknown deterministic metrics: "
                + ", ".join(sorted(unknown_metrics))
            )

        if (
            claim.kind in {ClaimKind.FACT, ClaimKind.CALCULATION}
            and not claim.evidence_ids
            and not claim.metric_ids
        ):
            raise ReportGroundingError(
                f"{claim.kind.value} claim requires evidence_ids or metric_ids"
            )

        referenced_evidence.update(claim.evidence_ids)

    evidence: list[EvidenceRef] = [
        known_evidence[source_id]
        for source_id in sorted(referenced_evidence)
    ]

    limitations = list(dict.fromkeys([*context.limitations, *report.limitations]))

    return report.model_copy(
        update={
            "symbol": context.symbol,
            "as_of": context.requested_as_of,
            "evidence": evidence,
            "limitations": limitations,
        }
    )
