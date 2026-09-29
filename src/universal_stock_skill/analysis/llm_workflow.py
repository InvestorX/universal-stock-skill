from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

from universal_stock_skill.analysis.context import (
    AnalysisContext,
    build_analysis_context,
)
from universal_stock_skill.analysis.grounding import ground_report
from universal_stock_skill.analysis.models import FinancialSnapshot
from universal_stock_skill.analysis.orchestrator import StockAnalysisDataBundle
from universal_stock_skill.analysis.report import StockAnalysisReport
from universal_stock_skill.evidence.collection import EvidenceItem
from universal_stock_skill.analysis.workflow import calculate_stock_metrics
from universal_stock_skill.llm import LLMProvider, LLMRequest, Message
from universal_stock_skill.runtime import validate_structured_response

DEFAULT_ANALYSIS_INSTRUCTION = (
    "Analyze the company using only the supplied point-in-time data."
)


@dataclass
class StockAnalysisWorkflow:
    provider: LLMProvider

    async def run(
        self,
        snapshot: FinancialSnapshot,
        *,
        instruction: str = DEFAULT_ANALYSIS_INSTRUCTION,
    ) -> StockAnalysisReport:
        """Backward-compatible snapshot-only workflow."""

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
                        f"Point-in-time context:\n"
                        f"{json.dumps(context, ensure_ascii=False)}"
                    ),
                ),
            ],
            response_schema=StockAnalysisReport.model_json_schema(),
            temperature=0.0,
        )

        response = await self.provider.generate(request)
        return validate_structured_response(response, StockAnalysisReport)

    async def run_bundle(
        self,
        bundle: StockAnalysisDataBundle,
        *,
        evidence_items: Sequence[EvidenceItem] = (),
        peer_bundles: Sequence[StockAnalysisDataBundle] = (),
        instruction: str = DEFAULT_ANALYSIS_INSTRUCTION,
    ) -> StockAnalysisReport:
        context = build_analysis_context(
            bundle,
            evidence_items=evidence_items,
            peer_bundles=peer_bundles,
        )
        return await self.run_context(context, instruction=instruction)

    async def run_context(
        self,
        context: AnalysisContext,
        *,
        instruction: str = DEFAULT_ANALYSIS_INSTRUCTION,
    ) -> StockAnalysisReport:
        context_json = json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
        )

        request = LLMRequest(
            messages=[
                Message(
                    role="system",
                    content=(
                        "You are executing a model-independent, point-in-time stock "
                        "analysis skill. Treat authoritative_facts, deterministic_metrics, "
                        "trends, and derivations exactly as supplied; do not recompute or "
                        "silently change them. Never invent evidence IDs, source metadata, "
                        "financial values, peer data, news, guidance, or catalysts. "
                        "For structured claims, use only evidence_ids and metric_ids that "
                        "exist in the supplied context. Every fact or calculation claim "
                        "must cite at least one evidence_id or metric_id. Interpretations "
                        "must be clearly phrased as interpretation. Scenarios must be "
                        "explicit assumptions, not factual predictions. If peer, news, "
                        "guidance, or catalyst evidence is absent, leave those conclusions "
                        "empty or state the limitation. Return a StockAnalysisReport that "
                        "conforms exactly to the requested schema."
                    ),
                ),
                Message(
                    role="user",
                    content=(
                        f"Task:\n{instruction}\n\n"
                        f"AnalysisContext:\n{context_json}"
                    ),
                ),
            ],
            response_schema=StockAnalysisReport.model_json_schema(),
            temperature=0.0,
        )

        response = await self.provider.generate(request)
        report = validate_structured_response(response, StockAnalysisReport)
        return ground_report(report, context)
