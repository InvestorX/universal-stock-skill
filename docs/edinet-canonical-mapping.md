# EDINET canonical financial mapping

[日本語](edinet-canonical-mapping.ja.md)

## Goal

Convert EDINET XBRL-to-CSV facts into stable, provider-neutral financial metric names without asking an LLM to guess which row means revenue, operating income, EPS, and so on.

~~~mermaid
flowchart LR
    CSV[EDINET CSV facts] --> M[Canonical mapper]
    M --> R[Exact taxonomy rules]
    R --> C[Canonical financial facts]
    C --> A[Stock analysis / metrics]
~~~

The mapper first uses known standard taxonomy element IDs. If an exact standard mapping is unavailable, a narrow company-extension fallback is allowed for revenue and operating income only.

## Canonical core

The initial set includes:

- revenue
- operating_income
- profit_before_tax
- net_income
- total_assets
- net_assets
- eps
- diluted_eps
- bps
- roe_official
- equity_ratio_official
- cf_operating
- cf_investing
- cf_financing
- cash

## Accounting standards

Each canonical fact preserves its source accounting standard:

- J-GAAP
- IFRS
- US-GAAP
- unknown

The canonical name makes downstream analysis uniform while the original element ID, item label, context, unit, and CSV location remain attached for provenance.

## Candidate selection

The mapper scores exact taxonomy matches deterministically.

Priority is given to:

1. explicit mapping priority
2. current-year facts
3. consolidated facts in AUTO mode
4. non-member contexts
5. expected period type
6. CurrentYear context IDs

If equally preferred candidates disagree in value, the mapper raises CanonicalMappingConflict instead of selecting one arbitrarily.

## Revenue semantics

revenue is not always economically identical across industries.

For example, some financial institutions report ordinary income where ordinary industrial companies report net sales. Such aliases carry a semantic note so downstream analysis can avoid naive peer comparisons.

## Extension fallback

Fallback matching is intentionally narrow.

- runs only after exact standard mapping fails
- accepts company-extension namespaces used by annual securities reports
- currently targets revenue, operating income, and net income
- requires SummaryOfBusinessResults or KeyFinancialData-style local names
- uses metric-specific exclusion tokens such as Intersegment, Cost, Gain, Loss, Proceeds, Ordinary, BeforeTax, Segment, PerShare, and Ratio
- records match_type=extension_fallback and keeps the original element ID

The next step is to validate these rules against real filings and then connect CanonicalFinancialSet to FinancialSnapshot.


## Accounting-standard inference

Company-extension element names do not always contain the accounting-standard token.

For extension fallback, the mapper therefore inspects current-year facts across the filing:

1. US-GAAP markers take precedence when current-year element IDs contain USGAAP / us-gaap.
2. IFRS is selected when current-year element IDs contain IFRS / ifrs-full.
3. Otherwise, a filing with current-year facts defaults to J-GAAP.
4. With no current-year evidence, the standard remains unknown.

Exact standard-taxonomy mappings still carry their explicitly declared accounting standard.


## Historical series

EDINET annual-report CSV commonly includes the current period together with prior-year restatements.

The mapper normalizes those contexts into year offsets:

| EDINET context | year_offset |
|---|---:|
| CurrentYear... | 0 |
| Prior1Year... | 1 |
| Prior2Year... | 2 |
| PriorNYear... | N |

`resolve_series(..., years=5)` returns a `CanonicalFinancialSeries` without asking an LLM to align periods.

The analysis layer can then calculate:

- year-over-year change
- CAGR using the oldest available positive base
- generic two-period averages

Growth rates whose base value is zero or negative are intentionally left unavailable rather than emitting misleading percentages.

Two-period averaging is generic. The runtime does **not** automatically treat `net_assets` as ROE equity because JP GAAP shareholders' equity and IFRS equity attributable to owners of parent are not identical accounting concepts.


## Mapping quality report

`evaluate_mapping_quality()` summarizes the current canonical result for validation and benchmark use.

It reports:

- requested metric count
- mapped metric count
- exact standard matches
- extension fallback matches
- missing metrics
- coverage ratio
- fallback ratio
- which metrics depended on fallback

This makes real-filing validation measurable instead of treating any non-empty output as success.
