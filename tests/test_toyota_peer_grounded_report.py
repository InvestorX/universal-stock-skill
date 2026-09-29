import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from universal_stock_skill.analysis.llm_workflow import StockAnalysisWorkflow
from universal_stock_skill.benchmark.automotive_peers import (
    toyota_automotive_peer_context,
)
from universal_stock_skill.benchmark.toyota_analysis import (
    toyota_reference_market_snapshot,
)
from universal_stock_skill.llm import LLMRequest, LLMResponse

JST = ZoneInfo("Asia/Tokyo")


class ToyotaPeerFakeProvider:
    async def generate(self, request: LLMRequest) -> LLMResponse:
        content = request.messages[-1].content
        context_json = content.split("AnalysisContext:\n", maxsplit=1)[1]
        context = json.loads(context_json)

        assert context["symbol"] == "7203"
        assert context["peer_metrics"]["peer:7203:revenue_yoy"] == pytest.approx(
            0.05512968,
            rel=1e-5,
        )
        assert context["peer_metrics"]["peer:7267:revenue_yoy"] == pytest.approx(
            0.0049722974
        )
        assert context["peer_metrics"]["peer:7201:revenue_yoy"] == pytest.approx(
            -0.0494985678
        )
        assert context["peer_metrics"]["peer:7267:operating_margin"] == pytest.approx(
            -0.019
        )
        assert context["peer_metrics"]["peer:7201:operating_margin"] == pytest.approx(
            0.005
        )

        evidence_ids = {item["source_id"] for item in context["evidence"]}
        assert "toyota:ir:fy2026-results" in evidence_ids
        assert "peer:7267:ir:fy2026-results" in evidence_ids
        assert "peer:7201:ir:fy2025-results" in evidence_ids

        return LLMResponse(
            text="",
            structured={
                "summary": (
                    "For the common year ended March 31, 2026, Toyota had "
                    "higher revenue growth, operating margin, and ROE than "
                    "the Honda and Nissan reference rows."
                ),
                "earnings": (
                    "Toyota revenue grew about 5.5%, versus about 0.5% for "
                    "Honda and a decline of about 4.9% for Nissan."
                ),
                "profitability": (
                    "Toyota operating margin was about 7.43% and ROE about "
                    "10.15%, while Honda reported -1.9% margin and -3.5% ROE "
                    "and Nissan reported 0.5% margin and -10.9% ROE."
                ),
                "financial_position": (
                    "No additional balance-sheet conclusion is asserted beyond "
                    "the deterministic peer values."
                ),
                "cash_flow": (
                    "Honda has a comparable cash-FCF reference in this fixture; "
                    "Nissan FCF yield is intentionally unavailable because its "
                    "published automobile-business FCF definition is not aligned."
                ),
                "valuation": (
                    "Reference-price valuation metrics are regression inputs. "
                    "Honda and Nissan have negative EPS in the common annual "
                    "period, so conventional PER is unavailable."
                ),
                "peer_comparison": (
                    "Toyota: revenue YoY ~5.5%, operating margin ~7.43%, ROE "
                    "~10.15%; Honda: ~0.5%, -1.9%, -3.5%; Nissan: ~-4.9%, "
                    "0.5%, -10.9%."
                ),
                "peer_analysis": {
                    "profitability": {
                        "text": (
                            "Toyota has the stronger profitability profile in "
                            "the supplied common-period comparison."
                        ),
                        "claim_ids": [
                            "peer-operating-margin",
                            "peer-roe",
                        ],
                    },
                    "valuation": {
                        "text": (
                            "Honda and Nissan conventional PER comparison is "
                            "unavailable because common-period EPS is negative."
                        ),
                        "claim_ids": ["peer-negative-per"],
                    },
                    "growth": {
                        "text": (
                            "Toyota has the higher revenue growth rate in the "
                            "supplied common-period comparison."
                        ),
                        "claim_ids": ["peer-revenue-growth"],
                    },
                    "competitive_position": {
                        "text": (
                            "The supplied profitability and growth metrics place "
                            "Toyota ahead of the two reference peers on those "
                            "specific dimensions."
                        ),
                        "claim_ids": [
                            "peer-revenue-growth",
                            "peer-operating-margin",
                            "peer-roe",
                        ],
                    },
                },
                "growth_drivers": [],
                "catalysts": [],
                "risks": [
                    (
                        "Honda and Nissan have negative EPS, so conventional "
                        "PER comparison is unavailable for this annual period."
                    )
                ],
                "scenarios": [],
                "claims": [
                    {
                        "claim_id": "peer-revenue-growth",
                        "text": (
                            "Toyota revenue growth was about 5.5%, versus about "
                            "0.5% for Honda and -4.9% for Nissan."
                        ),
                        "kind": "calculation",
                        "evidence_ids": [
                            "toyota:ir:fy2026-results",
                            "peer:7267:ir:fy2026-results",
                            "peer:7201:ir:fy2025-results",
                        ],
                        "metric_ids": [
                            "peer:7203:revenue_yoy",
                            "peer:7267:revenue_yoy",
                            "peer:7201:revenue_yoy",
                        ],
                    },
                    {
                        "claim_id": "peer-operating-margin",
                        "text": (
                            "Toyota operating margin was about 7.43%, versus "
                            "-1.9% for Honda and 0.5% for Nissan."
                        ),
                        "kind": "calculation",
                        "evidence_ids": [
                            "toyota:ir:fy2026-results",
                            "peer:7267:ir:fy2026-results",
                            "peer:7201:ir:fy2025-results",
                        ],
                        "metric_ids": [
                            "peer:7203:operating_margin",
                            "peer:7267:operating_margin",
                            "peer:7201:operating_margin",
                        ],
                    },
                    {
                        "claim_id": "peer-roe",
                        "text": (
                            "Toyota ROE was about 10.15%, while Honda and Nissan "
                            "were negative at about -3.5% and -10.9%."
                        ),
                        "kind": "calculation",
                        "evidence_ids": [
                            "toyota:ir:fy2026-results",
                            "peer:7267:ir:fy2026-results",
                            "peer:7201:ir:fy2025-results",
                        ],
                        "metric_ids": [
                            "peer:7203:roe",
                            "peer:7267:roe",
                            "peer:7201:roe",
                        ],
                    },
                    {
                        "claim_id": "peer-negative-per",
                        "text": (
                            "Honda and Nissan PER values are unavailable because "
                            "EPS is negative in the common annual period."
                        ),
                        "kind": "calculation",
                        "evidence_ids": [
                            "peer:7267:ir:fy2026-results",
                            "peer:7201:ir:fy2025-results",
                        ],
                        "metric_ids": [
                            "peer:7267:per",
                            "peer:7201:per",
                        ],
                    },
                    {
                        "claim_id": "nissan-fcf-not-comparable",
                        "text": (
                            "Nissan FCF yield is unavailable in this reference "
                            "comparison because the fixture does not treat its "
                            "automobile-business FCF as directly comparable."
                        ),
                        "kind": "interpretation",
                        "evidence_ids": [],
                        "metric_ids": [],
                    },
                ],
                "limitations": [
                    (
                        "All peer market prices are injected regression inputs, "
                        "not frozen historical-price claims."
                    ),
                    (
                        "Nissan free-cash-flow yield is intentionally unavailable "
                        "because the published FCF definition is not directly "
                        "comparable with the consolidated cash-FCF definition."
                    ),
                ],
                "evidence": [
                    {
                        "source_id": "invented:peer-source",
                        "title": "Must be discarded",
                    }
                ],
            },
            model="fake-toyota-peers",
        )


def reference_peer_context():
    return toyota_automotive_peer_context(
        toyota_reference_market_snapshot(
            price=3000,
            observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
        ),
        honda_price=1500,
        nissan_price=350,
    )


@pytest.mark.asyncio
async def test_toyota_peer_grounded_report_uses_real_peer_evidence() -> None:
    report = await StockAnalysisWorkflow(
        ToyotaPeerFakeProvider()
    ).run_context(reference_peer_context())

    assert report.symbol == "7203"
    assert report.peer_comparison is not None
    assert "Honda" in report.peer_comparison
    assert "Nissan" in report.peer_comparison
    assert report.peer_analysis is not None
    assert report.peer_analysis.profitability is not None
    assert report.peer_analysis.valuation is not None
    assert report.peer_analysis.growth is not None
    assert report.peer_analysis.competitive_position is not None
    assert report.peer_analysis.profitability.claim_ids == [
        "peer-operating-margin",
        "peer-roe",
    ]

    evidence_ids = {item.source_id for item in report.evidence}
    assert evidence_ids == {
        "toyota:ir:fy2026-results",
        "peer:7267:ir:fy2026-results",
        "peer:7201:ir:fy2025-results",
    }
    assert "invented:peer-source" not in evidence_ids

    claim_ids = {claim.claim_id for claim in report.claims}
    assert {
        "peer-revenue-growth",
        "peer-operating-margin",
        "peer-roe",
        "peer-negative-per",
        "nissan-fcf-not-comparable",
    } <= claim_ids

    assert not any(
        item == "Deterministic peer comparison data is unavailable."
        for item in report.limitations
    )
    assert any(
        "PER is therefore unavailable" in item
        for item in report.limitations
    )
