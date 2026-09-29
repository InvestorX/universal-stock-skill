# Provider adapters

The skill layer must not know which LLM vendor is in use.

## Contract

Every adapter implements:

```python
async def generate(request: LLMRequest) -> LLMResponse:
    ...
```

The runtime sends vendor-neutral:

- messages
- tool definitions
- optional JSON schema
- temperature

The adapter translates those into the provider's API.

## Capability negotiation

Each model/provider pair exposes `ProviderCapabilities`.

Current flags:

- `native_tool_calling`
- `structured_output`
- `json_schema`
- `parallel_tool_calls`

A future runtime layer will use these flags to select:

1. native provider feature when available
2. provider-neutral text/JSON fallback otherwise

## OpenAI-compatible adapter

`OpenAICompatibleProvider` targets the common Chat Completions API shape.

This is useful for:

- OpenAI-compatible hosted APIs
- local gateways
- vLLM servers configured with an OpenAI-compatible endpoint
- other servers that implement the same API shape

The adapter should not be confused with "OpenAI-only": it is a protocol compatibility layer.

## Native adapters

Native Anthropic and Gemini adapters can be added when native features are materially better than the compatibility route. They should still expose the same `LLMProvider` contract.
