from datetime import UTC, datetime

import pytest

from universal_stock_skill.analysis.llm_workflow import StockAnalysisWorkflow
from universal_stock_skill.analysis.models import FinancialSnapshot
from universal_stock_skill.llm import LLMRequest, LLMResponse


class FakeProvider:
    async def generate(self, request: LLMRequest) -> LLMResponse:
        assert request.response_schema is not None
        assert "calculated_metrics" in request.messages[-1].content
        return LLMResponse(
            text="",
            structured={
                "summary": "Sample summary",
                "earnings": "Sample earnings analysis",
                "profitability": "Sample profitability analysis",
                "financial_position": "Sample financial position",
                "cash_flow": "Sample cash flow analysis",
                "valuation": "Sample valuation analysis",
                "growth_drivers": ["driver"],
                "risks": ["risk"],
                "scenarios": ["scenario"],
                "evidence": [],
            },
            model="fake",
        )


@pytest.mark.asyncio
async def test_stock_analysis_workflow_calculates_before_llm() -> None:
    snapshot = FinancialSnapshot(
        symbol="DEMO",
        as_of=datetime(2026, 1, 1, tzinfo=UTC),
        price=1000.0,
        revenue=10000.0,
        operating_income=1000.0,
        net_income=500.0,
        eps=100.0,
        bps=500.0,
        average_equity=5000.0,
        operating_cash_flow=800.0,
        capital_expenditure=200.0,
        market_cap=10000.0,
    )

    report = await StockAnalysisWorkflow(FakeProvider()).run(snapshot)
    assert report.summary == "Sample summary"
    assert report.risks == ["risk"]
