from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

from universal_stock_skill.llm.base import LLMProvider, LLMRequest, LLMResponse
from universal_stock_skill.llm.capabilities import ProviderCapabilities


def _default_capabilities() -> ProviderCapabilities:
    return ProviderCapabilities(
        native_tool_calling=True,
        structured_output=True,
        json_schema=True,
        parallel_tool_calls=True,
    )


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    model: str
    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 120.0
    capabilities: ProviderCapabilities = field(default_factory=_default_capabilities)


class OpenAICompatibleProvider(LLMProvider):
    """Adapter for OpenAI-compatible Chat Completions APIs.

    This intentionally targets the common /v1/chat/completions shape so the
    same adapter can be used with hosted providers and many local gateways.
    """

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config

    def _build_payload(self, request: LLMRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "temperature": request.temperature,
        }

        if request.tools and self.config.capabilities.native_tool_calling:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in request.tools
            ]

        if request.response_schema and self.config.capabilities.json_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "skill_response",
                    "strict": True,
                    "schema": request.response_schema,
                },
            }
        elif request.response_schema and self.config.capabilities.structured_output:
            payload["response_format"] = {"type": "json_object"}

        return payload

    async def generate(self, request: LLMRequest) -> LLMResponse:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        url = f"{self.config.base_url.rstrip('/')}/v1/chat/completions"
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=self._build_payload(request))
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]
        text = choice.get("content") or ""

        structured: dict[str, Any] | None = None
        if request.response_schema and text:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    structured = parsed
            except json.JSONDecodeError:
                structured = None

        tool_calls: list[dict[str, Any]] = []
        for item in choice.get("tool_calls", []) or []:
            function = item.get("function", {})
            arguments = function.get("arguments", "{}")
            try:
                parsed_arguments = json.loads(arguments)
            except json.JSONDecodeError:
                parsed_arguments = {"_raw": arguments}

            tool_calls.append(
                {
                    "id": item.get("id"),
                    "name": function.get("name"),
                    "arguments": parsed_arguments,
                }
            )

        return LLMResponse(
            text=text,
            structured=structured,
            tool_calls=tool_calls,
            model=data.get("model", self.config.model),
            usage=data.get("usage") or {},
        )
