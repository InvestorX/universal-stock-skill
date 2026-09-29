from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class LLMRequest:
    messages: list[Message]
    tools: list[ToolDefinition] = field(default_factory=list)
    response_schema: dict[str, Any] | None = None
    temperature: float = 0.0


@dataclass(frozen=True)
class LLMResponse:
    text: str
    structured: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    """Vendor-neutral contract implemented by every model adapter."""

    async def generate(self, request: LLMRequest) -> LLMResponse:
        ...
