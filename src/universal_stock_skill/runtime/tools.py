from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from universal_stock_skill.llm import ToolDefinition


ToolHandler = Callable[[dict[str, Any]], dict[str, Any] | Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class RegisteredTool:
    definition: ToolDefinition
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        if definition.name in self._tools:
            raise ValueError(f"tool already registered: {definition.name}")
        self._tools[definition.name] = RegisteredTool(definition, handler)

    def definitions(self) -> list[ToolDefinition]:
        return [item.definition for item in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")

        result = self._tools[name].handler(arguments)
        if inspect.isawaitable(result):
            result = await result

        if not isinstance(result, dict):
            raise TypeError(f"tool {name} must return dict, got {type(result).__name__}")
        return result
