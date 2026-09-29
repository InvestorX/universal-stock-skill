# Market Dataモデル

[English](market-data.md) | **日本語**

## 目的

株価系データを特定Providerへ依存させず、EDINET財務データと結合する前にPoint-in-Time安全性を保証します。

~~~mermaid
flowchart LR
    P[Market Data Provider] --> M[MarketSnapshot]
    M --> S[Point-in-Time Selector]
    S --> B[Snapshot Bridge Inputs]
    B --> F[FinancialSnapshot]
~~~

## MarketSnapshot

保持項目:

- symbol
- observed_at
- price
- currency
- source
- optional market_cap
- optional shares_outstanding

時価総額がなく発行済株式数がある場合は、Python側で決定論的に次を計算します。

`market_cap = price × shares_outstanding`

Providerが明示したmarket_capは上書きしません。

## Point-in-Time選択

`select_market_snapshot(...)` は次の条件を満たすデータだけを候補にします。

- symbol一致
- observed_at <= as_of
- `require_market_cap=True` の場合は時価総額あり

条件を満たす最新値を採用し、未来の株価は絶対に使いません。

## FinancialSnapshot Bridge

`build_snapshot_bridge_inputs()` でMarketSnapshotと次の派生値を結合します。

- 平均自己資本
- CapEx
- NOPAT
- 平均投下資本

その結果を既存の `SnapshotBridgeInputs` に変換し、EDINET Canonical側と結合できます。

## 互換性

既存の `PriceDataSource` Protocolは残します。今後のProvider実装では、より多くの市場情報を扱える `MarketDataSource` を優先します。
