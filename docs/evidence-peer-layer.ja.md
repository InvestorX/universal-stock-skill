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

## Provider方針

Core Runtimeは特定News APIを必須にしません。

今後、同じEvidenceItem ContractのAdapterとして次を追加できます。

- TDnet / 適時開示
- 企業IR
- Licensed News Provider
- Host AgentによるWeb Research
- 社内Research DB

どのProviderでも同じPoint-in-Time Guardを必ず通します。
