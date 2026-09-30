import pytest

from universal_stock_skill.llm import (
    LLMRequest,
    LLMResponse,
    Message,
    ProviderCapabilities,
)
from universal_stock_skill.llm.portable import PortableLLMProvider, PortableOutputError


class TextOnlyFakeProvider:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.last_request: LLMRequest | None = None

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.last_request = request
        return LLMResponse(text=self.response_text, model="text-only")


@pytest.mark.asyncio
async def test_structured_schema_falls_back_to_prompted_json() -> None:
    inner = TextOnlyFakeProvider('{"value": 42}')
    provider = PortableLLMProvider(
        inner,
        ProviderCapabilities(
            native_tool_calling=False,
            structured_output=False,
            json_schema=False,
        ),
    )

    response = await provider.generate(
        LLMRequest(
            messages=[Message(role="user", content="Return a value.")],
            response_schema={
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
            },
        )
    )

    assert response.structured == {"value": 42}
    assert inner.last_request is not None
    assert inner.last_request.response_schema is None
    assert "JSON Schema" in inner.last_request.messages[-1].content


@pytest.mark.asyncio
async def test_markdown_fenced_json_is_tolerated() -> None:
    inner = TextOnlyFakeProvider('```json\n{"value": 42}\n```')
    provider = PortableLLMProvider(inner, ProviderCapabilities())

    response = await provider.generate(
        LLMRequest(
            messages=[Message(role="user", content="Return a value.")],
            response_schema={"type": "object"},
        )
    )
    assert response.structured == {"value": 42}


@pytest.mark.asyncio
async def test_missing_json_is_rejected() -> None:
    inner = TextOnlyFakeProvider("I cannot provide JSON.")
    provider = PortableLLMProvider(inner, ProviderCapabilities())

    with pytest.raises(PortableOutputError):
        await provider.generate(
            LLMRequest(
                messages=[Message(role="user", content="Return a value.")],
                response_schema={"type": "object"},
            )
        )
