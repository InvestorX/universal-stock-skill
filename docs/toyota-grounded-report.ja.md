# トヨタ7203 Grounded Report Regression

[English](toyota-grounded-report.md) | **日本語**

## 目的

トヨタ7203の実在企業Reference Caseを使い、Report生成までの完全な経路をRegression Testします。

~~~mermaid
flowchart LR
    T[Toyota Reference Fact]
    --> A[ToyotaReferenceAnalysis]
    A --> C[AnalysisContext]
    C --> L[LLM / Host Agent]
    L --> R[Structured StockAnalysisReport]
    R --> G[Grounding Validator]
    C --> G
    G --> O[Grounded Toyota Report]
~~~

Toyota専用の答えを本番コードへハードコードしません。本番側が行うのは汎用AnalysisContextの生成だけです。Test Providerが通常のModel Adapterと同じようにStructured Reportを返し、Grounding Validatorで検証します。

## Toyota AnalysisContext

~~~python
context = toyota_reference_analysis_context(
    toyota_reference_market_snapshot(
        price=3000,
        observed_at=observed_at,
    )
)
~~~

ここで注入する株価はRegression入力であり、Toyotaの実際の過去株価を主張するものではありません。

信頼済みEvidence ID:

~~~text
toyota:ir:fy2026-results
toyota:ir:fy2027-q1-results
toyota:ir:2026-buyback
market:reference:toyota-market-input:<observed_at>
~~~

主な決定論的Metric ID:

~~~text
metric:operating_margin
metric:per
metric:pbr
metric:roe
metric:free_cash_flow
metric:free_cash_flow_yield

trend:revenue
trend:operating_income
trend:net_income

derivation:average_equity
derivation:capital_expenditure
derivation:effective_tax_rate
derivation:nopat
~~~

## RegressionするReport Claim

Test Reportでは次のClaimを根拠付きで検証します。

- FY2026売上高の前年比
- FY2026営業利益の前年比
- 営業利益率・ROE
- Free Cash Flow
- Reference価格でのPER / PBR
- 2026年8月の自己株取得
- FY2027第1四半期決算の公表

最終ReportのEvidence一覧はAnalysisContextから再構築します。Modelが架空のEvidence metadataを返しても破棄されます。

## 未対応Source

Toyota Reference Contextには、意図的にDeterministic Peer BundleとNews Provider Evidenceを入れていません。

そのためReportには次のLimitationが残ります。

- Peer比較なし
- News Evidenceなし

Toyota公式IRとTimely Disclosureは存在するため、それらは「不足」と扱いません。

## Context確認

~~~bash
python scripts/inspect_toyota_analysis_context.py \
  --price 3000 \
  --as-of 2026-09-29T15:30:00+09:00
~~~

Standalone LLM / Host Agentへ実際に渡るJSONをそのまま確認できます。
