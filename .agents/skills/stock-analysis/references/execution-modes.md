# Execution modes / 実行モード

## Host-agent mode / Host-Agentモード

This is the default for an installed Agent Skill.

The current host agent supplies reasoning, model selection, authentication, and native tools. The skill does not require a separate LLM endpoint.

Agent Skillとして導入した場合の標準です。現在の親Agentが推論、model選択、認証、Native Toolを提供します。Skillのためだけに別endpointを指定しません。

Use host-native capabilities first:

- web or browser search
- MCP / connectors
- local files
- shell / terminal
- the host model itself

Deterministic calculations and temporal checks should still be delegated to Python when helpers are available.

## Standalone runtime mode / Standalone Runtimeモード

Use only when model routing must be controlled by the Python application itself.

Examples:

- cross-model benchmarks
- RRSI candidate evaluation
- batch analysis
- provider experiments
- application embedding

Only this mode needs Provider Adapter endpoint/model credentials.

Cross-Model Benchmark、RRSI Candidate評価、Batch処理等でPython側からmodel routingを明示制御する場合だけProvider Adapterを使います。
