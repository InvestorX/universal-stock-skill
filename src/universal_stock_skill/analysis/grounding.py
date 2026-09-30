from __future__ import annotations

from universal_stock_skill.analysis.context import AnalysisContext
from universal_stock_skill.analysis.report import (
    ClaimKind,
    EvidenceRef,
    GroundedClaim,
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

    claim_ids = [claim.claim_id for claim in report.claims]
    if len(claim_ids) != len(set(claim_ids)):
        raise ReportGroundingError("claim_id values must be unique")

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

    _validate_peer_analysis(report, context)

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


def _validate_peer_analysis(
    report: StockAnalysisReport,
    context: AnalysisContext,
) -> None:
    peer_analysis = report.peer_analysis
    if peer_analysis is None:
        return
    if not context.peer_metrics:
        raise ReportGroundingError(
            "structured peer analysis requires peer metrics in AnalysisContext"
        )

    known_claims = {
        claim.claim_id: claim
        for claim in report.claims
    }
    sections = {
        "profitability": peer_analysis.profitability,
        "valuation": peer_analysis.valuation,
        "growth": peer_analysis.growth,
        "cash_flow": peer_analysis.cash_flow,
        "competitive_position": peer_analysis.competitive_position,
    }

    for section_name, section in sections.items():
        if section is None:
            continue

        unknown_claim_ids = set(section.claim_ids) - set(known_claims)
        if unknown_claim_ids:
            raise ReportGroundingError(
                f"peer analysis {section_name} references unknown claim_ids: "
                + ", ".join(sorted(unknown_claim_ids))
            )

        for claim_id in section.claim_ids:
            claim = known_claims[claim_id]
            if not _is_peer_grounded(claim):
                raise ReportGroundingError(
                    f"peer analysis {section_name} claim {claim_id} "
                    "must reference a peer metric or peer evidence ID"
                )


def _is_peer_grounded(claim: GroundedClaim) -> bool:
    return any(
        reference.startswith("peer:")
        for reference in [*claim.evidence_ids, *claim.metric_ids]
    )
