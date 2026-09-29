# Toyota 7203 reference case

[日本語](toyota-reference-case.ja.md)

## Purpose

Toyota Motor Corporation (security code 7203) is the first real-company regression case in the project.

The case freezes a small set of values from Toyota's official FY2026 financial summary and selected 2026 investor-relations disclosures so deterministic calculations, evidence handling, and point-in-time guards can be regression-tested without making CI depend on live websites.

~~~mermaid
flowchart LR
    T[Toyota official IR]
    --> R[Toyota reference case]
    R --> F[Frozen FY2025 / FY2026 facts]
    R --> E[Official qualitative evidence]
    F --> X[Regression calculations]
    E --> G[Point-in-Time EvidenceCollector]
    X --> B[Benchmark / RRSI checks]
    G --> B
~~~

## Source period

Fiscal year ended March 31, 2026.

Accounting standard: IFRS.

Official FY2026 values frozen in the case include:

| Item | FY2026 | FY2025 | Unit |
|---|---:|---:|---|
| Sales revenues | 50,684,952 | 48,036,704 | million JPY |
| Operating income | 3,766,216 | 4,795,586 | million JPY |
| Income before income taxes | 5,152,996 | 6,414,590 | million JPY |
| Net income attributable to Toyota | 3,848,098 | 4,765,086 | million JPY |
| Total assets | 105,522,331 | 93,601,350 | million JPY |
| Toyota shareholders' equity | 39,918,854 | 35,924,826 | million JPY |
| Operating cash flow | 5,472,920 | 3,696,934 | million JPY |
| Income tax expense | 1,167,234 | 1,624,835 | million JPY |
| Basic EPS | 295.25 | 359.56 | JPY/share |
| BPS | 3,062.82 | 2,753.09 | JPY/share |
| ROE | 10.1% | 13.6% | percent |
| Operating margin | 7.4% | 10.0% | percent |

Primary source:

- Toyota Motor Corporation FY2026 Financial Summary, May 8, 2026
- https://global.toyota/pages/global_toyota/ir/financial-results/2026_4q_summary_en.pdf

## Regression checks

The tests independently recalculate:

- FY2026 operating margin
- revenue year-over-year change
- operating-income year-over-year change
- parent-attributable net-income year-over-year change
- two-period average owners' equity
- ROE from parent-attributable income and average owners' equity
- effective tax rate
- NOPAT

The recalculated rounded values must agree with Toyota's published ratios and changes where the official summary provides them.

This deliberately checks the runtime's accounting arithmetic against a real IFRS issuer rather than only synthetic data.

## Qualitative evidence

The reference case also includes official Toyota IR evidence available by the case cutoff:

1. FY2026 financial results, May 8, 2026
2. FY2027 first-quarter financial-results announcement, August 4, 2026
3. August 4, 2026 share-repurchase / treasury-stock-retirement notice

The buyback notice states a maximum repurchase of 500 million shares for up to JPY 1,000 billion, with a repurchase period from August 5, 2026 through August 4, 2027, and retirement of 200 million treasury shares.

Source:

- https://global.toyota/pages/global_toyota/ir/stock/share/commonstock_20260804_en.pdf

These records pass through the same EvidenceCollector and PointInTimeGuard used by normal runtime evidence.

## Market price policy

The reference case intentionally does **not** freeze a stock price.

Point-in-time valuation should continue to obtain price and market capitalization from MarketDataSource / J-Quants for the requested analysis timestamp.

This keeps the benchmark fixture focused on official company facts and avoids treating an arbitrary historical market price as a permanent company fact.

## Inspect the fixture

~~~bash
python scripts/inspect_toyota_reference.py
~~~

This prints the complete frozen case as JSON.


## Reference analysis adapter

The Toyota case can now be converted into CanonicalFinancialSet / CanonicalFinancialSeries and passed through the same deterministic derivation and metric code used by normal EDINET analysis.

The adapter converts Toyota's published million-JPY values into base JPY before assembly.

For FY2026 FCF regression, cash CapEx is defined from the consolidated cash-flow statement as:

~~~text
fixed assets excluding equipment leased to others  2,148,192 million JPY
equipment leased to others                         2,766,352 million JPY
intangible assets                                    378,804 million JPY
-------------------------------------------------------------
cash CapEx                                         5,293,348 million JPY
~~~

This is intentionally different from Toyota's segment-note "Capital expenditures" measure because FinancialSnapshot free cash flow uses cash outflows.

The real-company case also changed average-equity derivation behavior. For IFRS / US-GAAP, two-period owners' equity now takes precedence over back-solving from rounded official ROE.

Example with an explicitly supplied reference market price:

~~~bash
python scripts/inspect_toyota_reference_analysis.py \
  --price 3000 \
  --as-of 2026-09-29T15:30:00+09:00
~~~

The price above is only a regression input, not a frozen claim about Toyota's real market price. Production analysis should pass the J-Quants MarketSnapshot for the requested timestamp.
