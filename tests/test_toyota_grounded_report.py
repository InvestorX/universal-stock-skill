import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from universal_stock_skill.analysis.llm_workflow import StockAnalysisWorkflow
from universal_stock_skill.benchmark.toyota_analysis import (
    toyota_reference_analysis_context,
    toyota_reference_market_snapshot,
)
from universal_stock_skill.llm import LLMRequest, LLMResponse


JST = ZoneInfo("Asia/Tokyo")


class ToyotaGroundedFakeProvider:
    async def generate(self, request: LLMRequest) -> LLMResponse:
        assert request.response_schema is not None
        content = request.messages[-1].content
        context_json = content.split("AnalysisContext:\n", maxsplit=1)[1]
        context = json.loads(context_json)

        assert context["symbol"] == "7203"
        assert context["deterministic_metrics"]["metric:operating_margin"] == pytest.approx(
            0.0743063937
        )
        assert context["deterministic_metrics"]["metric:per"] == pytest.approx(
            10.16088061
        )
        assert context["trends"]["trend:revenue"]["year_over_year"] == pytest.approx(
            0.05512968,
            rel=1e-5,
        )

        evidence_ids = {item["source_id"] for item in context["evidence"]}
        assert "toyota:ir:fy2026-results" in evidence_ids
        assert "toyota:ir:fy2027-q1-results" in evidence_ids
        assert "toyota:ir:2026-buyback" in evidence_ids
        assert (
            "market:reference:toyota-market-input:"
            "2026-09-29T15:30:00+09:00"
        ) in evidence_ids

        return LLMResponse(
            text="",
            structured={
                "summary": (
                    "Toyota's FY2026 revenue increased, while operating income "
                    "and parent-attributable profit declined year over year."
                ),
                "earnings": (
                    "FY2026 revenue increased about 5.5% year over year, while "
                    "operating income fell about 21.5%."
                ),
                "profitability": (
                    "The deterministic operating margin is about 7.43% and "
                    "ROE is about 10.15%."
                ),
                "financial_position": (
                    "No additional balance-sheet conclusion is asserted beyond "
                    "the supplied deterministic facts."
                ),
                "cash_flow": (
                    "Operating cash flow less cash CapEx produced positive "
                    "free cash flow of JPY 179.572 billion."
                ),
                "valuation": (
                    "At the injected regression price of JPY 3,000, deterministic "
                    "PER is about 10.16x and PBR about 0.98x."
                ),
                "peer_comparison": None,
                "growth_drivers": [],
                "catalysts": [
                    (
                        "Toyota disclosed a share repurchase authorization of up "
                        "to 500 million shares and JPY 1 trillion, together with "
                        "retirement of 200 million treasury shares."
                    )
                ],
                "risks": [
                    "FY2026 operating income declined materially year over year."
                ],
                "scenarios": [],
                "claims": [
                    {
                        "claim_id": "revenue-yoy",
                        "text": "FY2026 revenue increased about 5.5% year over year.",
                        "kind": "calculation",
                        "evidence_ids": ["toyota:ir:fy2026-results"],
                        "metric_ids": ["trend:revenue"],
                    },
                    {
                        "claim_id": "operating-income-yoy",
                        "text": (
                            "FY2026 operating income declined about 21.5% "
                            "year over year."
                        ),
                        "kind": "calculation",
                        "evidence_ids": ["toyota:ir:fy2026-results"],
                        "metric_ids": ["trend:operating_income"],
                    },
                    {
                        "claim_id": "profitability",
                        "text": (
                            "Operating margin is about 7.43% and ROE about 10.15%."
                        ),
                        "kind": "calculation",
                        "evidence_ids": ["toyota:ir:fy2026-results"],
                        "metric_ids": [
                            "metric:operating_margin",
                            "metric:roe",
                        ],
                    },
                    {
                        "claim_id": "free-cash-flow",
                        "text": "Deterministic free cash flow is JPY 179.572 billion.",
                        "kind": "calculation",
                        "evidence_ids": ["toyota:ir:fy2026-results"],
                        "metric_ids": [
                            "metric:free_cash_flow",
                            "derivation:capital_expenditure",
                        ],
                    },
                    {
                        "claim_id": "reference-valuation",
                        "text": (
                            "At the injected JPY 3,000 regression price, PER is "
                            "about 10.16x and PBR about 0.98x."
                        ),
                        "kind": "calculation",
                        "evidence_ids": [
                            (
                                "market:reference:toyota-market-input:"
                                "2026-09-29T15:30:00+09:00"
                            )
                        ],
                        "metric_ids": [
                            "metric:per",
                            "metric:pbr",
                        ],
                    },
                    {
                        "claim_id": "buyback",
                        "text": (
                            "Toyota authorized repurchases of up to 500 million "
                            "shares for up to JPY 1 trillion and retirement of "
                            "200 million treasury shares."
                        ),
                        "kind": "fact",
                        "evidence_ids": ["toyota:ir:2026-buyback"],
                        "metric_ids": [],
                    },
                    {
                        "claim_id": "fy2027-q1-publication",
                        "text": (
                            "Toyota published FY2027 first-quarter financial "
                            "results on August 4, 2026."
                        ),
                        "kind": "fact",
                        "evidence_ids": ["toyota:ir:fy2027-q1-results"],
                        "metric_ids": [],
                    },
                ],
                "limitations": [
                    "No deterministic peer comparison was supplied.",
                    "No news-provider evidence was supplied.",
                ],
                "evidence": [
                    {
                        "source_id": "invented:toyota-source",
                        "title": "This must be discarded",
                    }
                ],
            },
            model="fake-toyota",
        )


def reference_context():
    market = toyota_reference_market_snapshot(
        price=3000,
        observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
    )
    return toyota_reference_analysis_context(market)


def test_toyota_reference_context_contains_real_ir_and_deterministic_ids() -> None:
    context = reference_context()

    assert context.symbol == "7203"
    assert "toyota:ir:fy2026-results" in context.evidence_ids
    assert "toyota:ir:fy2027-q1-results" in context.evidence_ids
    assert "toyota:ir:2026-buyback" in context.evidence_ids
    assert "metric:per" in context.metric_ids
    assert "trend:operating_income" in context.metric_ids
    assert "derivation:capital_expenditure" in context.metric_ids

    assert "News evidence is unavailable." in context.limitations
    assert (
        "Deterministic peer comparison data is unavailable."
        in context.limitations
    )
    assert not any(
        "Company IR / management-guidance evidence is unavailable" in item
        for item in context.limitations
    )
    assert not any(
        "Timely-disclosure / catalyst evidence is unavailable" in item
        for item in context.limitations
    )


@pytest.mark.asyncio
async def test_toyota_grounded_report_rebuilds_trusted_evidence() -> None:
    report = await StockAnalysisWorkflow(
        ToyotaGroundedFakeProvider()
    ).run_context(reference_context())

    assert report.symbol == "7203"
    assert report.as_of == datetime(2026, 9, 29, 23, 59, tzinfo=JST)

    evidence_ids = {item.source_id for item in report.evidence}
    assert evidence_ids == {
        "toyota:ir:fy2026-results",
        "toyota:ir:fy2027-q1-results",
        "toyota:ir:2026-buyback",
        (
            "market:reference:toyota-market-input:"
            "2026-09-29T15:30:00+09:00"
        ),
    }
    assert "invented:toyota-source" not in evidence_ids

    claim_ids = {claim.claim_id for claim in report.claims}
    assert {
        "revenue-yoy",
        "operating-income-yoy",
        "profitability",
        "free-cash-flow",
        "reference-valuation",
        "buyback",
        "fy2027-q1-publication",
    } <= claim_ids

    assert any("500 million" in item for item in report.catalysts)
    assert any(
        "Reference market price is an injected regression input" in item
        for item in report.limitations
    )
