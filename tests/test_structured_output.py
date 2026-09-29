import pytest
from pydantic import BaseModel

from universal_stock_skill.llm import LLMResponse
from universal_stock_skill.runtime import StructuredOutputError, validate_structured_response


class Example(BaseModel):
    value: int


def test_native_structured_payload_is_validated() -> None:
    response = LLMResponse(text="", structured={"value": 42})
    result = validate_structured_response(response, Example)
    assert result.value == 42


def test_json_text_is_provider_neutral_fallback() -> None:
    response = LLMResponse(text='{"value": 42}')
    result = validate_structured_response(response, Example)
    assert result.value == 42


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(StructuredOutputError):
        validate_structured_response(LLMResponse(text="not json"), Example)
