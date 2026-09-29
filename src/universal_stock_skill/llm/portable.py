from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any

from universal_stock_skill.llm.base import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    Message,
)
from universal_stock_skill.llm.capabilities import ProviderCapabilities


class PortableOutputError(ValueError):
    pass


@dataclass
class PortableLLMProvider(LLMProvider):
    """Adds provider-neutral fallbacks around an arbitrary LLMProvider.

    The first fallback implemented here is structured JSON output. If a model
    has no native structured-output capability, the JSON Schema is injected
    into the prompt and the returned text is parsed back into a JSON object.
    """

    provider: LLMProvider
    capabilities: ProviderCapabilities

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if (
            request.response_schema is None
            or self.capabilities.json_schema
            or self.capabilities.structured_output
        ):
            return await self.provider.generate(request)

        schema_text = json.dumps(
            request.response_schema,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        fallback_message = Message(
            role="system",
            content=(
                "The requested model endpoint does not provide native structured output. "
                "Return exactly one JSON object and no surrounding prose or Markdown. "
                "The JSON object must conform to this JSON Schema:\n"
                f"{schema_text}"
            ),
        )

        fallback_request = replace(
            request,
            messages=[*request.messages, fallback_message],
            response_schema=None,
        )
        response = await self.provider.generate(fallback_request)

        if response.structured is not None:
            return response

        structured = _parse_json_object(response.text)
        return replace(response, structured=structured)


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        if start < 0:
            raise PortableOutputError("model response contains no JSON object")

        decoder = json.JSONDecoder()
        try:
            parsed, _ = decoder.raw_decode(stripped[start:])
        except json.JSONDecodeError as exc:
            raise PortableOutputError("model response does not contain valid JSON") from exc

    if not isinstance(parsed, dict):
        raise PortableOutputError("structured fallback requires a JSON object")
    return parsed
