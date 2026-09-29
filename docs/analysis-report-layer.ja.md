# Analysis Report Layer

[English](analysis-report-layer.md) | **日本語**

## 目的

決定論的に生成したStockAnalysisDataBundleをLLMが解釈しやすいContextへ変換しつつ、LLMによるEvidence捏造や計算値の改変を防ぎます。

~~~mermaid
flowchart LR
    B[StockAnalysisDataBundle]
    --> C[AnalysisContext]
    C --> L[Host Agent / LLM Provider]
    L --> R[Structured StockAnalysisReport]
    R --> G[Grounding Validator]
    C --> G
    G --> O[Evidence-grounded Report]
~~~

## AnalysisContext

Contextでは次を分離します。

- authoritative facts
- deterministic metrics
- deterministic trends / derivations
- limitations

Evidenceや計算値には安定したIDを付けます。

例:

~~~text
edinet:S100XXXX
market:jquants:v2:2026-09-29T15:30:00+09:00
metric:per
metric:roe
trend:revenue
derivation:average_equity
~~~

LLMは既知IDを参照できますが、新しいIDを勝手に作ってはいけません。

## Claim種別

Structured claimを次に分類します。

- fact
- calculation
- interpretation
- assumption

fact / calculationは、少なくとも1つの既知evidence IDまたはdeterministic metric IDを参照する必要があります。

interpretationでは与えられた事実からの解釈を記述できますが、新しい事実を紛れ込ませてはいけません。

Scenarioは事実としての予測ではなく、assumptionとして明示します。

## Evidence再構築

最終的なEvidence metadataをLLMに委ねません。

モデルがevidence objectを返しても、Grounding Layerはいったん破棄し、信頼済みAnalysisContextから最終Evidence一覧を再構築します。

そのため、JSONに架空のEDINET docID、URL、公開日時、Market Sourceを書くだけでは最終Reportへ混入できません。

## Evidenceが存在しない場合

現在の決定論的Bundleには次があります。

- EDINET有報
- J-Quants MarketSnapshot
- 決定論的な財務計算・Trend

一方、まだ自動では含みません。

- Peer企業データ
- News
- Management Guidance
- 定性的Catalyst Evidence

Evidenceがない項目をLLMが創作して埋めてはいけません。空欄にするかlimitationを明示します。

## Standalone Runtime

StockAnalysisWorkflowは3つの入口を持ちます。

~~~python
workflow.run(snapshot)       # 旧Snapshot-only
workflow.run_bundle(bundle) # 推奨Grounded path
workflow.run_context(ctx)   # 生成済AnalysisContext
~~~

Standaloneではrun_bundle()を推奨します。

Structured Reportは二段階で検証します。

1. Pydantic / JSON Schema
2. AnalysisContextに対するGrounding Validation

## Host AgentでSkill実行する場合

Codex、Claude Code、Antigravity、Hermes上でPortable Agent Skillとして使う場合は、現在のHost Agent自身が推論エンジンです。

ただし契約は同じです。

- 決定論的計算値をauthoritativeとして扱う
- 重要な事実claimをEvidenceへ紐付ける
- 存在しないSource種別を創作しない
- assumption / interpretationを明示する
