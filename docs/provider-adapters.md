# Provider adapters and execution modes

[日本語](provider-adapters.ja.md)

## Host-agent mode is the default for installed skills

When stock-analysis is installed into Codex, Claude Code, Antigravity CLI, or Hermes Agent, the current agent itself is the reasoning provider. No extra LLM endpoint is required.

~~~mermaid
flowchart LR
    S[SKILL.md] --> H[Host Agent]
    T[Host-native tools] --> H
    P[Deterministic Python] --> H
    H --> O[Analysis output]
~~~

The skill should prefer capabilities already available to the host: browser/search, MCP, local files, shell, and the host model.

## Standalone mode

Provider Adapters exist for programmatic runs that intentionally control model routing.

~~~mermaid
flowchart LR
    C[CLI / Benchmark / RRSI] --> R[SkillRuntime]
    R --> A[LLMProvider]
    A --> OAI[OpenAI-compatible]
    A --> N[Future native adapters]
    R --> P[Deterministic Python]
~~~

Use standalone mode for cross-model evaluation, batch runs, or embedding the runtime in another application.

## Contract

Every standalone adapter implements:

~~~python
async def generate(request: LLMRequest) -> LLMResponse:
    ...
~~~

The runtime sends vendor-neutral messages, tools, optional JSON schema, and sampling configuration.

## Capability negotiation

ProviderCapabilities currently represents:

- native_tool_calling
- structured_output
- json_schema
- parallel_tool_calls

PortableLLMProvider supplies a text-to-JSON fallback when native structured output is unavailable.

## OpenAI-compatible adapter

OpenAICompatibleProvider targets the common Chat Completions shape and can be used with compatible hosted or local gateways. It is an optional standalone protocol adapter, not a requirement for Agent Skill installation.

## Native adapters

Native adapters should be added only when a provider's native behavior materially improves capability or reliability. They must preserve the same provider-neutral contract.
