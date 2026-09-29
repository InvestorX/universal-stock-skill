# J-Quants market-data adapter

[日本語](jquants-market.ja.md)

## Why J-Quants

J-Quants API is operated by JPX and provides historical Japanese equity data through API V2.

Authentication uses an API key in the x-api-key header.

~~~text
x-api-key: <JQUANTS_API_KEY>
~~~

The default base URL is:

~~~text
https://api.jquants.com/v2
~~~

The adapter reads JQUANTS_API_KEY from the environment when JQuantsConfig.from_env() is used. Users do not need to configure an endpoint URL for normal use.

## Endpoints

Price and market capitalization are intentionally separated.

~~~mermaid
flowchart LR
    A[as_of + security code] --> P[/equities/bars/daily]
    A --> V[/equities/valuation]
    P --> C[Unadjusted close C]
    V --> M[MktCap]
    C --> S[MarketSnapshot]
    M --> S
~~~

- /equities/bars/daily supplies the absolute market price.
- /equities/valuation supplies market capitalization when a same-date row is available.

The valuation endpoint is preferred for market capitalization instead of depending on the daily-bar MktCap field.

## Point-in-time behavior

Tokyo Stock Exchange currently closes at 15:30 JST.

A daily close is represented as observed at 15:30 JST on its trading date. If as_of is earlier than that time, the same-day close is not eligible.

The adapter searches a configurable lookback window and selects the latest eligible daily close.

Market capitalization is attached only when the valuation row has the same trading date as the selected close. It is never silently borrowed from another date.

## Price basis

MarketSnapshot.price uses the unadjusted close C, with Close accepted as a compatibility alias.

This is deliberate: PER, PBR, and other absolute valuation ratios should use the actual price formed on that trading date. Adjusted close belongs in historical-return and chart series.

## Market-cap units

J-Quants valuation MktCap is interpreted as millions of JPY. The adapter converts it to JPY before constructing MarketSnapshot.

## Example

~~~python
from universal_stock_skill.data import JQuantsConfig, JQuantsMarketDataSource

source = JQuantsMarketDataSource(JQuantsConfig.from_env())
snapshot = await source.get_market_snapshot("7203", as_of)
await source.aclose()
~~~

The Agent Skill itself never embeds a J-Quants API key.


## Diagnostic CLI

With JQUANTS_API_KEY set:

~~~bash
python scripts/inspect_jquants_market.py 7203 \
  --as-of 2026-09-29T16:00:00+09:00
~~~

The command prints the selected point-in-time MarketSnapshot as JSON.
