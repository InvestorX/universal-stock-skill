# Provider Adapterと実行モード

[English](provider-adapters.md) | **日本語**

## Skill導入時はHost-Agentモードが標準

stock-analysisをCodex、Claude Code、Antigravity CLI、Hermes Agentに導入した場合、**現在そのSkillを実行しているAgent自身が推論Provider**です。別のLLM endpointは不要です。

~~~mermaid
flowchart LR
    S[SKILL.md] --> H[親Agent]
    T[親AgentのNative Tool] --> H
    P[決定論的Python] --> H
    H --> O[銘柄分析結果]
~~~

Browser/Search、MCP、Local File、Shell、モデル推論など、親Agentが既に持っている能力を優先します。

## Standaloneモード

Provider Adapterは、モデルルーティングをプログラム側から明示制御したい場合に使います。

~~~mermaid
flowchart LR
    C[CLI / Benchmark / RRSI] --> R[SkillRuntime]
    R --> A[LLMProvider]
    A --> OAI[OpenAI-compatible]
    A --> N[将来のNative Adapter]
    R --> P[決定論的Python]
~~~

主用途はCross-Model評価、Batch実行、RRSI Candidate評価、別アプリへのRuntime組込みです。

## 契約

Standalone Adapterは共通して次を実装します。

~~~python
async def generate(request: LLMRequest) -> LLMResponse:
    ...
~~~

Runtimeからはベンダー非依存のmessages、tool定義、任意JSON Schema、sampling設定を渡します。

## Capability negotiation

現在のProviderCapabilities:

- native_tool_calling
- structured_output
- json_schema
- parallel_tool_calls

Native Structured Outputが無い場合、PortableLLMProviderがtextからJSON Objectへ戻すfallbackを提供します。

## OpenAI-compatible Adapter

OpenAICompatibleProviderは一般的なChat Completions互換形状を対象にします。Agent Skill導入の必須条件ではなく、Standalone Runtime用の任意Adapterです。

## Native Adapter

Provider固有機能に実質的なメリットがある場合だけ追加し、外側には同一のProvider-neutral contractを維持します。
