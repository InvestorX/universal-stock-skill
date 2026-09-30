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

## 構造化Peer Analysis

Peer Metricが存在する場合、後方互換の自由記述 `peer_comparison` に加えて、最終Reportで `peer_analysis` を使用できます。

`peer_analysis` は次のGrounded Subsectionを持ちます。

- profitability
- valuation
- growth
- cash flow
- competitive position

各Subsectionは本文と1つ以上の `claim_ids` を持ちます。IDはReport内のClaimを参照し、リンクされた各Claimは少なくとも1つの `peer:` Metric IDまたは `peer:` Evidence IDを参照しなければなりません。

~~~json
{
  "peer_analysis": {
    "profitability": {
      "text": "供給された比較では対象銘柄のMarginとROEが高い。",
      "claim_ids": ["peer-operating-margin", "peer-roe"]
    },
    "valuation": {
      "text": "赤字Peerでは通常のPER比較を利用できない。",
      "claim_ids": ["peer-negative-per"]
    }
  }
}
~~~

Grounding Layerは次を拒否します。

- `AnalysisContext.peer_metrics` が空なのに構造化Peer Analysisを出す
- 存在しないClaim IDを参照する
- Peer Sectionから参照しているのに `peer:` Metric/Evidenceを1つも持たないClaim

これによりPeer Narrativeを、AnalysisContextで使った決定論的な比較Rowへ追跡できます。

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
