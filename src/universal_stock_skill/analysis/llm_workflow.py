from __future__ import annotations

import json
from dataclasses import dataclass

from universal_stock_skill.analysis.models import FinancialSnapshot
from universal_stock_skill.analysis.report import StockAnalysisReport
from universal_stock_skill.analysis.workflow import calculate_stock_metrics
from universal_stock_skill.llm import LLMProvider, LLMRequest, Message
from universal_stock_skill.runtime import validate_structured_response


@dataclass
class StockAnalysisWorkflow:
    provider: LLMProvider

    async def run(
        self,
        snapshot: FinancialSnapshot,
        *,
        instruction: str = "Analyze the company using only the supplied point-in-time data.",
    ) -> StockAnalysisReport:
        metrics = calculate_stock_metrics(snapshot)

        context = {
            "snapshot": snapshot.model_dump(mode="json"),
            "calculated_metrics": metrics.model_dump(mode="json"),
        }

        request = LLMRequest(
            messages=[
                Message(
                    role="system",
                    content=(
                        "You are executing a model-independent stock analysis skill. "
                        "All supplied calculated metrics are authoritative. "
                        "Do not invent sources or facts. Distinguish fact from interpretation. "
                        "If evidence is missing, state the limitation rather than filling the gap."
                    ),
                ),
                Message(
                    role="user",
                    content=(
                        f"Task:\n{instruction}\n\n"
                        f"Point-in-time context:\n{json.dumps(context, ensure_ascii=False)}"
                    ),
                ),
            ],
            response_schema=StockAnalysisReport.model_json_schema(),
            temperature=0.0,
        )

        response = await self.provider.generate(request)
        return validate_structured_response(response, StockAnalysisReport)
