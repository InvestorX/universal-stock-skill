from datetime import UTC, datetime

import pytest

from universal_stock_skill.analysis.context import AnalysisContext
from universal_stock_skill.analysis.grounding import (
    ReportGroundingError,
    ground_report,
)
from universal_stock_skill.analysis.report import (
    ClaimKind,
    EvidenceRef,
    GroundedClaim,
    StockAnalysisReport,
)


def context() -> AnalysisContext:
    return AnalysisContext(
        symbol="7203",
        requested_as_of=datetime(2026, 9, 29, 12, 0, tzinfo=UTC),
        evidence=[
            EvidenceRef(
                source_id="edinet:CORR",
                title="Demo Corp annual filing CORR",
                published_at=datetime(2026, 7, 1, 1, 0, tzinfo=UTC),
            ),
            EvidenceRef(
                source_id="market:jquants:v2:2026-09-29T06:30:00+00:00",
                title="7203 market snapshot",
                published_at=datetime(2026, 9, 29, 6, 30, tzinfo=UTC),
            ),
        ],
        authoritative_facts={"financial_snapshot": {"revenue": 1000}},
        deterministic_metrics={
            "metric:per": 12.0,
            "metric:roe": 0.1,
        },
        trends={
            "trend:revenue": {
                "current_value": "1100",
                "prior_value": "1000",
                "year_over_year": 0.1,
            }
        },
        derivations={
            "average_equity": "700",
            "average_equity_method": "official_roe_backsolve",
        },
        limitations=["No peer evidence is available."],
    )


def report_with_claims(*claims: GroundedClaim) -> StockAnalysisReport:
    return StockAnalysisReport(
        summary="Summary",
        earnings="Earnings",
        profitability="Profitability",
        financial_position="Financial position",
        cash_flow="Cash flow",
        valuation="Valuation",
        claims=list(claims),
        limitations=["Model limitation."],
        evidence=[
            EvidenceRef(
                source_id="invented:source",
                title="Invented source",
                url="https://example.invalid",
            )
        ],
    )


def test_ground_report_rebuilds_evidence_from_context() -> None:
    report = report_with_claims(
        GroundedClaim(
            claim_id="c1",
            text="Revenue increased year over year.",
            kind=ClaimKind.CALCULATION,
            evidence_ids=["edinet:CORR"],
            metric_ids=["trend:revenue"],
        ),
        GroundedClaim(
            claim_id="c2",
            text="PER is 12x.",
            kind=ClaimKind.CALCULATION,
            metric_ids=["metric:per"],
        ),
    )

    grounded = ground_report(report, context())

    assert grounded.symbol == "7203"
    assert grounded.as_of == datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
    assert [item.source_id for item in grounded.evidence] == ["edinet:CORR"]
    assert "invented:source" not in {item.source_id for item in grounded.evidence}
    assert grounded.limitations == [
        "No peer evidence is available.",
        "Model limitation.",
    ]


def test_unknown_evidence_id_is_rejected() -> None:
    report = report_with_claims(
        GroundedClaim(
            claim_id="c1",
            text="Unsupported filing fact.",
            kind=ClaimKind.FACT,
            evidence_ids=["edinet:UNKNOWN"],
        )
    )

    with pytest.raises(ReportGroundingError, match="unknown evidence"):
        ground_report(report, context())


def test_unknown_metric_id_is_rejected() -> None:
    report = report_with_claims(
        GroundedClaim(
            claim_id="c1",
            text="Unsupported metric.",
            kind=ClaimKind.CALCULATION,
            metric_ids=["metric:invented"],
        )
    )

    with pytest.raises(ReportGroundingError, match="unknown deterministic metrics"):
        ground_report(report, context())


def test_fact_or_calculation_requires_reference() -> None:
    report = report_with_claims(
        GroundedClaim(
            claim_id="c1",
            text="PER is low.",
            kind=ClaimKind.CALCULATION,
        )
    )

    with pytest.raises(ReportGroundingError, match="requires evidence_ids or metric_ids"):
        ground_report(report, context())


def test_interpretation_can_be_explicit_without_new_fact_reference() -> None:
    report = report_with_claims(
        GroundedClaim(
            claim_id="c1",
            text="The margin profile appears resilient.",
            kind=ClaimKind.INTERPRETATION,
        )
    )

    grounded = ground_report(report, context())

    assert grounded.claims[0].kind == ClaimKind.INTERPRETATION
