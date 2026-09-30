# Toyota 7203 grounded report regression

[日本語](toyota-grounded-report.ja.md)

## Goal

Use the frozen Toyota 7203 real-company reference case to exercise the complete report path:

~~~mermaid
flowchart LR
    T[Toyota reference facts]
    --> A[ToyotaReferenceAnalysis]
    A --> C[AnalysisContext]
    C --> L[LLM / Host Agent]
    L --> R[Structured StockAnalysisReport]
    R --> G[Grounding Validator]
    C --> G
    G --> O[Grounded Toyota report]
~~~

This regression does not hard-code a Toyota answer into production logic. Production code only builds a generic AnalysisContext. The test provider is responsible for producing a structured report, exactly like any other model adapter.

## Toyota AnalysisContext

Use:

~~~python
context = toyota_reference_analysis_context(
    toyota_reference_market_snapshot(
        price=3000,
        observed_at=observed_at,
    )
)
~~~

The injected market price is a regression input, not a claim about Toyota's actual historical share price.

The context exposes trusted evidence IDs including:

~~~text
toyota:ir:fy2026-results
toyota:ir:fy2027-q1-results
toyota:ir:2026-buyback
market:reference:toyota-market-input:<observed_at>
~~~

Deterministic metric IDs include:

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

## Regression report claims

The test report must ground claims such as:

- FY2026 revenue growth
- FY2026 operating-income decline
- operating margin and ROE
- free cash flow
- reference-price PER / PBR
- August 2026 share-repurchase authorization
- FY2027 first-quarter results publication

The final report evidence list is reconstructed from AnalysisContext. Any evidence metadata invented by the model is discarded.

## Unsupported areas

The Toyota reference context intentionally has no deterministic peer bundle and no licensed/news-provider evidence.

The report therefore preserves limitations for:

- peer comparison
- news evidence

Toyota official IR and timely-disclosure evidence are present, so those source classes are not reported as missing.

## Inspect the context

~~~bash
python scripts/inspect_toyota_analysis_context.py \
  --price 3000 \
  --as-of 2026-09-29T15:30:00+09:00
~~~

The command prints the exact JSON context that a standalone LLM or host agent would receive.
