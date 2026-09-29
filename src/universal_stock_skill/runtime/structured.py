from __future__ import annotations

import json
import typing

from pydantic import BaseModel, ValidationError

from universal_stock_skill.llm import LLMResponse


TModel = typing.TypeVar("TModel", bound=BaseModel)


class StructuredOutputError(ValueError):
    pass


def validate_structured_response(response: LLMResponse, model: type[TModel]) -> TModel:
    """Validate an LLM response against a Pydantic model.

    Native structured output is preferred. JSON text is accepted as a provider-neutral
    fallback so models without schema-native APIs can still participate.
    """

    payload = response.structured

    if payload is None:
        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise StructuredOutputError("response is not valid JSON") from exc

        if not isinstance(parsed, dict):
            raise StructuredOutputError("structured response must be a JSON object")
        payload = parsed

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise StructuredOutputError(str(exc)) from exc
