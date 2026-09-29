# Data source architecture

Market-data providers are adapters, just like LLM providers.

The stock-analysis skill should depend on internal protocols rather than vendor-specific APIs.

## Internal interfaces

- `FinancialDataSource`
- `DisclosureDataSource`
- `PriceDataSource`

Every evidence-bearing data source should return enough metadata to enforce point-in-time analysis.

At minimum:

- stable source identifier
- source type
- publication timestamp
- retrieval timestamp
- URL when available

## Japanese disclosure sources

### EDINET

EDINET is the natural source for statutory filings and XBRL-backed financial disclosure.
The current EDINET site states that API use requires registration and an API key and refers users to the EDINET API Specification Version 2.

Implementation should therefore keep EDINET credentials outside Skill definitions and inject them into a data-source adapter.

### TDnet

JPX provides a TDnet API service for timely disclosure information. The published service material describes separate index and document APIs.

TDnet API is a contracted data service, so the runtime must not assume that every installation has access to it. A free/public fallback source can be implemented separately where licensing permits.

## Point-in-time rule

Fetched information is not automatically eligible for analysis.

`PointInTimeGuard` rejects a source when:

```text
source.published_at > analysis.as_of
```

This check belongs in deterministic runtime code, not in an LLM prompt.
