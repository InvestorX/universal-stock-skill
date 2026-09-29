# End-to-end stock analysis data bundle

[日本語](e2e-stock-analysis.ja.md)

## Goal

Build a deterministic stock-analysis data bundle from only a security code and an as-of timestamp.

~~~mermaid
flowchart LR
    I[security code + as_of]
    --> D[EDINET filing discovery]
    D --> R[annual report + corrections]
    R --> C[Canonical current + series]

    I --> J[J-Quants MarketSnapshot]

    C --> Q[Mapping quality / readiness]
    C --> T[YoY / CAGR]
    C --> A[Financial derivations]
    J --> A

    A --> F[FinancialSnapshot]
    F --> M[StockMetrics]

    Q --> O[StockAnalysisDataBundle]
    T --> O
    M --> O
    R --> O
    J --> O
~~~

## Filing discovery

AnnualFilingDiscovery scans EDINET submission dates backwards from the requested as-of date.

It collects matching annual reports and correction reports for the security code. Scanning stops when the latest annual report visible at the requested timestamp is found.

Because the scan runs backwards from as_of, correction reports submitted after the original annual report are collected before the original is reached. AnnualFilingResolver then follows parentDocID relationships and selects the latest reachable correction that was already public at as_of.

The default lookback is 550 days and can be overridden.

## Orchestrator

StockAnalysisOrchestrator combines:

- AnnualFilingDiscovery
- EDINETCanonicalPipeline
- MarketDataSource

It returns StockAnalysisDataBundle containing:

- requested symbol and as-of timestamp
- selected filing provenance
- MarketSnapshot
- canonical mapping quality
- FinancialSnapshot readiness
- historical trends
- derived financial inputs and derivation methods
- FinancialSnapshot
- StockMetrics

No LLM is used to retrieve, align, select, or calculate these values.

## CLI

Set:

~~~text
EDINET_API_KEY
JQUANTS_API_KEY
~~~

Then run:

~~~bash
python scripts/analyze_stock.py 7203 \
  --as-of 2026-09-29T23:00:00+09:00 \
  --years 5
~~~

The result is JSON suitable for a stock-analysis Agent Skill or any other LLM host.

Normal use does not require endpoint URLs. Provider adapters own their default endpoints; the host supplies credentials and capabilities.

## Point-in-time contract

The requested as_of timestamp governs both sides:

- EDINET filings and corrections must have been published by as_of
- J-Quants must return a MarketSnapshot observed at or before as_of

The output preserves requested_as_of separately from the market snapshot observed_at so consumers can see the exact price timestamp used.
