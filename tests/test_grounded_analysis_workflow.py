import json
from datetime import UTC, datetime

import pytest

from universal_stock_skill.analysis.context import AnalysisContext
from universal_stock_skill.analysis.llm_workflow import StockAnalysisWorkflow
from universal_stock_skill.analysis.report import EvidenceRef
from universal_stock_skill.llm import LLMRequest, LLMResponse


class GroundedFakeProvider:
    async def generate(self, request: LLMRequest) -> LLMResponse:
        assert request.response_schema is not None
        content = request.messages[-1].content
        assert "AnalysisContext:" in content

        context_json = content.split("AnalysisContext:\n", maxsplit=1)[1]
        context = json.loads(context_json)
        assert context["symbol"] == "7203"
        assert context["deterministic_metrics"]["metric:per"] == 12.0
        assert context["trends"]["trend:revenue"]["year_over_year"] == 0.1

        return LLMResponse(
            text="",
            structured={
                "summary": "Revenue grew and valuation is measurable.",
                "earnings": "Revenue increased year over year.",
                "profitability": "ROE is 10%.",
                "financial_position": "No additional balance-sheet conclusion.",
                "cash_flow": "No additional cash-flow conclusion.",
                "valuation": "PER is 12x.",
                "peer_comparison": None,
                "growth_drivers": [],
                "catalysts": [],
                "risks": [],
                "scenarios": [],
                "claims": [
                    {
                        "claim_id": "revenue-growth",
                        "text": "Revenue increased 10% year over year.",
                        "kind": "calculation",
                        "evidence_ids": ["edinet:CORR"],
                        "metric_ids": ["trend:revenue"],
                    },
                    {
                        "claim_id": "valuation",
                        "text": "PER is 12x.",
                        "kind": "calculation",
                        "evidence_ids": [
                            "market:jquants:v2:2026-09-29T06:30:00+00:00"
                        ],
                        "metric_ids": ["metric:per"],
                    },
                ],
                "limitations": ["No peer comparison was performed."],
                "evidence": [
                    {
                        "source_id": "invented:model-source",
                        "title": "Should be discarded",
                    }
                ],
            },
            model="fake",
        )


def analysis_context() -> AnalysisContext:
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
        authoritative_facts={"financial_snapshot": {"revenue": 1100}},
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
        derivations={"average_equity": "700"},
        limitations=["No peer, news, guidance, or catalyst evidence is available."],
    )


@pytest.mark.asyncio
async def test_grounded_workflow_validates_and_rebuilds_evidence() -> None:
    report = await StockAnalysisWorkflow(GroundedFakeProvider()).run_context(
        analysis_context()
    )

    assert report.symbol == "7203"
    assert report.as_of == datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
    assert {item.source_id for item in report.evidence} == {
        "edinet:CORR",
        "market:jquants:v2:2026-09-29T06:30:00+00:00",
    }
    assert "invented:model-source" not in {
        item.source_id for item in report.evidence
    }
    assert report.claims[0].metric_ids == ["trend:revenue"]
    assert report.limitations == [
        "No peer, news, guidance, or catalyst evidence is available.",
        "No peer comparison was performed.",
    ]
