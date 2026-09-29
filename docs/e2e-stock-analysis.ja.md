# End-to-End銘柄分析Data Bundle

[English](e2e-stock-analysis.md) | **日本語**

## 目的

証券コードとas_ofだけを入口に、銘柄分析用の構造化データを決定論的に生成します。

~~~mermaid
flowchart LR
    I[証券コード + as_of]
    --> D[EDINET有報Discovery]
    D --> R[有報 + 訂正報告書]
    R --> C[Canonical当期 + 時系列]

    I --> J[J-Quants MarketSnapshot]

    C --> Q[Mapping品質 / Readiness]
    C --> T[前年比 / CAGR]
    C --> A[財務派生値]
    J --> A

    A --> F[FinancialSnapshot]
    F --> M[StockMetrics]

    Q --> O[StockAnalysisDataBundle]
    T --> O
    M --> O
    R --> O
    J --> O
~~~

## 有報Discovery

AnnualFilingDiscoveryは指定as_ofの日付からEDINET提出日を過去方向へ探索します。

証券コードが一致する有価証券報告書と訂正報告書を収集し、指定時刻までに公開済みの最新年次有報が見つかった時点で探索を終了します。

as_ofから逆向きに探索するため、有報提出後に出た訂正報告書は元有報へ到達する前に収集済みになります。その後AnnualFilingResolverがparentDocIDのchainを追い、as_of時点で利用可能な最新訂正版を選択します。

標準lookbackは550日で変更可能です。

## Orchestrator

StockAnalysisOrchestratorは次を結合します。

- AnnualFilingDiscovery
- EDINETCanonicalPipeline
- MarketDataSource

StockAnalysisDataBundleには次を含めます。

- 証券コード / requested as_of
- 採用した有報・訂正版のprovenance
- MarketSnapshot
- Canonical Mapping品質
- FinancialSnapshot Readiness
- 時系列Trend
- 派生財務値とDerivation method
- FinancialSnapshot
- StockMetrics

取得・期間合わせ・書類選択・財務計算にLLMを使いません。

## CLI

環境変数:

~~~text
EDINET_API_KEY
JQUANTS_API_KEY
~~~

を設定し、

~~~bash
python scripts/analyze_stock.py 7203 \
  --as-of 2026-09-29T23:00:00+09:00 \
  --years 5
~~~

を実行すると、stock-analysis Skillや任意LLM Hostへ渡せるJSONを生成します。

通常利用ではendpoint URLを指定しません。Provider Adapter側が標準endpointを持ち、Hostはcredentialとcapabilityを供給します。

## Point-in-Time Contract

requested as_ofをEDINET・市場データの両方へ適用します。

- EDINET有報・訂正報告書はas_ofまでに公開済みであること
- J-Quants MarketSnapshotはobserved_at <= as_ofであること

出力ではrequested_as_ofとMarketSnapshotのobserved_atを別々に保持するため、どの時点の価格を使ったか確認できます。
