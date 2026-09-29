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
- currently targets revenue and operating income
- requires SummaryOfBusinessResults or KeyFinancialData-style local names
- excludes Intersegment, Segment, Cost, Expense, PerShare, Ratio, and similar false-positive tokens
- records match_type=extension_fallback and keeps the original element ID

The next step is to validate these rules against real filings and then connect CanonicalFinancialSet to FinancialSnapshot.
