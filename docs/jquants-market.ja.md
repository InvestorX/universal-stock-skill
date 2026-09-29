# J-Quants Market Data Adapter

[English](jquants-market.md) | **日本語**

## J-Quantsを使う理由

J-Quants APIはJPXが提供する日本株向け金融データAPIです。

V2ではx-api-key headerによるAPI key認証を使います。

~~~text
x-api-key: <JQUANTS_API_KEY>
~~~

標準Base URL:

~~~text
https://api.jquants.com/v2
~~~

JQuantsConfig.from_env()を使うと、環境変数JQUANTS_API_KEYからkeyを読み込みます。通常利用ではendpoint URLを毎回指定する必要はありません。

## 使用Endpoint

株価と時価総額は意図的に分離します。

~~~mermaid
flowchart LR
    A[as_of + 証券コード] --> P[/equities/bars/daily]
    A --> V[/equities/valuation]
    P --> C[調整前終値 C]
    V --> M[MktCap]
    C --> S[MarketSnapshot]
    M --> S
~~~

- /equities/bars/daily は絶対価格として使う終値を提供
- /equities/valuation は同一取引日のデータがある場合に時価総額を提供

時価総額はdaily bar側のMktCapへ依存せず、valuation endpointを優先します。

## Point-in-Time

現在の東京証券取引所の大引けは15:30 JSTです。

日足終値のobserved_atを取引日の15:30 JSTとして扱います。そのためas_ofが15:30より前なら同日の終値は利用しません。

設定されたlookback期間内からas_of以前で最新の終値を選びます。

時価総額は、選択された終値と同一取引日のvaluation rowだけを採用します。別日の時価総額を黙って流用しません。

## 株価Basis

MarketSnapshot.priceは調整前終値Cを利用します。互換用にCloseも受け付けます。

PER/PBR等の絶対valuationでは、その日に実際に形成された価格を使うためです。AdjCは長期リターンやChart用Price Series側で扱います。

## 時価総額の単位

J-Quants valuationのMktCapは百万円単位として受け取り、MarketSnapshotへ入れる前にJPYへ変換します。

## 使用例

~~~python
from universal_stock_skill.data import JQuantsConfig, JQuantsMarketDataSource

source = JQuantsMarketDataSource(JQuantsConfig.from_env())
snapshot = await source.get_market_snapshot("7203", as_of)
await source.aclose()
~~~

Agent Skill本体へJ-Quants API keyを埋め込みません。
