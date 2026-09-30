from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from universal_stock_skill.llm import LLMProvider, LLMRequest, Message


@dataclass
class SkillRuntime:
    """Minimal model-independent runtime.

    The first implementation deliberately keeps orchestration small. Tool dispatch,
    structured-output repair and provider capability negotiation will be layered on
    top of this contract.
    """

    provider: LLMProvider

    async def run(self, instruction: str, context: dict[str, Any] | None = None) -> str:
        context = context or {}
        request = LLMRequest(
            messages=[
                Message(
                    role="system",
                    content=(
                        "You execute a stock-analysis skill. "
                        "Treat supplied deterministic values as authoritative, "
                        "separate facts from interpretation, and never invent evidence."
                    ),
                ),
                Message(
                    role="user",
                    content=f"Instruction:\n{instruction}\n\nContext:\n{context}",
                ),
            ]
        )
        response = await self.provider.generate(request)
        return response.text
