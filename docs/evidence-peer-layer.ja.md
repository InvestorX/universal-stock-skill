# Qualitative Evidence / Peer Comparison Layer

[English](evidence-peer-layer.md) | **日本語**

## 目的

特定のNews Vendorや開示APIへ固定せず、決定論的な銘柄分析へPeer比較・News・適時開示・IR Evidenceを追加します。

~~~mermaid
flowchart LR
    H[Host Agent / Provider]
    --> E[EvidenceItem]
    E --> C[EvidenceCollector]
    C --> G[Point-in-Time Guard + Dedup]

    P1[対象Bundle] --> PC[Peer Comparison]
    P2[Peer Bundle] --> PC
    P3[Peer Bundle] --> PC

    G --> A[AnalysisContext]
    PC --> A
    A --> L[Host Agent / LLM]
    L --> R[Grounded Report]
~~~

## EvidenceItem

Qualitative Evidenceは、信頼済みSourceRecordに次を付けたものです。

- symbol
- excerpt
- tags

SourceRecordには引き続き次を保持します。

- source_id
- source_type
- title
- published_at
- retrieved_at
- optional effective_at
- URL
- content hash
- metadata

既存source_type:

- filing
- timely_disclosure
- price
- news
- company_ir
- other

そのため、Codex / Claude Code / Antigravity / HermesなどのHost Agentが、自身のBrowser / Search / MCPで取得した情報をEvidenceItemへ変換できます。別LLMや特定News endpointの設定は不要です。

## EvidenceCollector

EvidenceCollectorは複数のEvidenceSourceを受け取れます。

各結果について次を検証します。

- symbol一致
- published_at <= as_of
- timezone-aware timestamp

content_hashがある場合はそれを使って重複排除し、なければsource_idで重複排除します。

同一Contentが複数Sourceから得られた場合は、より新しいpublished_atを採用します。最終結果は新しい順です。

Providerが未来情報を返した場合は、黙って混ぜずErrorにします。

## Peer Comparison

Peer比較には、すでに生成済みのStockAnalysisDataBundleを使用します。

全Bundleは次を満たす必要があります。

- symbolが重複しない
- requested_as_ofが完全一致

比較指標には決定論的IDを付与します。

~~~text
peer:7203:per
peer:6758:per
peer:6758:pbr
peer:6758:roe
peer:6758:operating_margin
peer:6758:free_cash_flow_yield
peer:6758:revenue_yoy
~~~

これによりLLMへ比較Metricを再計算させません。

Peer側の有報・Market provenanceも、次のようなnamespace付きEvidence IDでAnalysisContextへ追加します。

~~~text
peer:6758:edinet:S100XXXX
peer:6758:market:jquants:v2:...
~~~

## 決定論的な相対ポジショニング

`PeerComparisonSet` から決定論的な `PeerPositioningSet` を生成できます。順位、中央値、Peer平均をLLMの自由計算に任せません。

現在の対象Metricと数値順:

- PER: 昇順
- PBR: 昇順
- ROE: 降順
- 営業利益率: 降順
- FCF Yield: 降順
- 売上高YoY: 降順

各Metricについて次を保持します。

- 対象銘柄の値
- 順位と比較可能企業数
- 対象銘柄を含むComparison Set中央値
- 中央値との差
- 対象銘柄を除くPeer平均
- Peer平均との差

比較可能な値が2つ未満の場合は順位を出しません。欠損値は順位計算から除外し、完全同値は同順位にします。

Grounding可能な安定IDも `peer_metrics` に追加します。

~~~text
peer:7203:position:operating_margin:rank
peer:7203:position:operating_margin:available_count
peer:7203:position:operating_margin:comparison_median
peer:7203:position:operating_margin:delta_to_median
peer:7203:position:operating_margin:peer_mean
peer:7203:position:operating_margin:delta_to_peer_mean
~~~

差分はすべて `対象銘柄 - 比較値` です。符号は純粋な数値差であり、優劣判定ではありません。また順位1位は、そのMetricで定義した数値順の先頭という意味で、総合投資評価や「最良」を意味しません。

## AnalysisContextへの追加

build_analysis_context()へoptionalで渡します。

~~~python
context = build_analysis_context(
    subject_bundle,
    evidence_items=evidence_items,
    peer_bundles=peer_bundles,
)
~~~

供給された場合:

- qualitative evidenceをauthoritative_factsへ追加
- 信頼済みEvidenceRefをGrounding対象へ追加
- Peer Comparisonをauthoritative_factsへ追加
- Peer Metric IDをGrounding可能にする
- 実際に存在するEvidence種別だけlimitationsを減らす

Peerデータを渡しただけでNewsやIR Evidenceが存在することにはしません。Newsがなければ「News evidence is unavailable」は残ります。

## 汎用Subject + Peer Orchestration

Productionでも、1つのPoint-in-Time cutoffからSubjectと全Peerをまとめて生成できます。

~~~python
peer = PeerAnalysisOrchestrator(stock_orchestrator)
result = await peer.analyze(
    "7203",
    peer_symbols=["7267", "7201"],
    as_of=as_of,
    years=5,
)
context = result.build_context()
~~~

OrchestratorはSymbolを正規化し、Provider I/O前に重複を拒否し、全銘柄へ完全に同じ `as_of` を適用します。Peerの指定順を保持したまま決定論的な `PeerComparisonSet` を生成します。

CLI:

~~~bash
python scripts/analyze_peers.py 7203 \
  --peers 7267 7201 \
  --as-of 2026-09-29T15:30:00+09:00
~~~

Production Metric PipelineではEPSが0以下の場合、PERを利用不可とします。負のPERを通常の「低PER」と誤解する経路を防ぎます。

## Provider方針

Core Runtimeは特定News APIを必須にしません。

今後、同じEvidenceItem ContractのAdapterとして次を追加できます。

- TDnet / 適時開示
- 企業IR
- Licensed News Provider
- Host AgentによるWeb Research
- 社内Research DB

どのProviderでも同じPoint-in-Time Guardを必ず通します。
