# Market data model

[日本語](market-data.ja.md)

## Goal

Keep market-price data provider-neutral and point-in-time safe before it is combined with EDINET financials.

~~~mermaid
flowchart LR
    P[Market data provider] --> M[MarketSnapshot]
    M --> S[Point-in-time selector]
    S --> B[Snapshot bridge inputs]
    B --> F[FinancialSnapshot]
~~~

## MarketSnapshot

A market snapshot stores:

- symbol
- observed_at
- price
- currency
- source
- optional market_cap
- optional shares_outstanding

If market capitalization is absent but shares outstanding is known, it is derived deterministically as:

`market_cap = price × shares_outstanding`

An explicit market capitalization is never overwritten.

## Point-in-time selection

`select_market_snapshot(...)` only considers records whose:

- symbol matches
- observed_at is at or before the requested as-of timestamp
- market capitalization is present when `require_market_cap=True`

The latest eligible snapshot is selected. Future quotes are never used.

## FinancialSnapshot bridge

`build_snapshot_bridge_inputs()` combines market data with derived filing-side inputs such as:

- average equity
- capital expenditure
- NOPAT
- average invested capital

It then produces the existing `SnapshotBridgeInputs` consumed by the EDINET canonical bridge.

## Compatibility

The existing `PriceDataSource` protocol remains available. New provider implementations should prefer `MarketDataSource` when they can supply richer metadata.
