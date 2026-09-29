# Deterministic financial derivations

[日本語](financial-derivations.ja.md)

## Goal

Derive the remaining FinancialSnapshot inputs from canonical filing data without asking an LLM to infer accounting values.

~~~mermaid
flowchart LR
    C[Canonical current facts] --> D[Derivation layer]
    S[Canonical historical series] --> D
    M[MarketSnapshot] --> A[Snapshot assembler]
    D --> A
    A --> F[FinancialSnapshot]
    F --> K[PER / PBR / ROE / FCF Yield / optional ROIC]
~~~

## Average equity

When IFRS or US-GAAP canonical equity values are available for both the current and prior periods, the preferred method is a two-period average:

~~~text
average_equity = (current_owners_equity + prior_owners_equity) / 2
~~~

This avoids error introduced by back-solving from an officially published ROE that may already be rounded.

If safe two-period owners' equity is unavailable, the runtime may reconstruct the denominator from official ROE:

~~~text
average_equity = net_income / official_roe
~~~

ROE normalization is conservative:

- values between 0 and 1 are treated as decimal ratios
- values above 1 require an explicit percent-style unit
- ambiguous large unitless ratios are rejected

JP GAAP net assets are not automatically substituted for owners' equity. For JP GAAP, official-ROE backsolve therefore remains the safe fallback until an explicit owners-equity mapping is available.

The Toyota FY2026 real-company regression case is what exposed this ordering issue: its published ROE is 10.1%, while averaging FY2025/FY2026 Toyota shareholders' equity reproduces the rounded 10.1% without reverse-engineering from the rounded ratio.

## Capital expenditure

Capital expenditure is derived in this order:

1. combined property, plant and equipment plus intangible-asset purchase fact
2. otherwise the sum of available PPE and intangible-asset purchase cash-flow facts

Cash outflows are normalized to a positive CapEx amount before FinancialSnapshot is built.

Supported standard facts include JP GAAP cash-flow taxonomy elements and selected IFRS / IFRS-full purchase elements.

## NOPAT

NOPAT is calculated only when all of the following are available:

- operating income
- profit before tax
- income taxes

~~~text
effective_tax_rate = income_taxes / profit_before_tax
NOPAT = operating_income × (1 - effective_tax_rate)
~~~

The derivation is rejected when:

- profit before tax is zero or negative
- income taxes are negative
- the resulting tax rate is outside 0 to 1

This intentionally avoids manufacturing a normalised tax rate from unusual tax-benefit periods.

## Average invested capital

Average invested capital remains unavailable in the automatic derivation layer for now.

The runtime does not yet claim that a partial debt mapping is equivalent to complete invested capital. Until interest-bearing debt and lease-liability coverage is validated across accounting standards, ROIC remains optional.

## FinancialSnapshot assembler

Use:

~~~python
result = assemble_financial_snapshot(
    current=canonical_bundle.current,
    series=canonical_bundle.series,
    market=market_snapshot,
)
~~~

The assembler:

1. validates required filing-side canonical metrics
2. derives average equity, CapEx and optional NOPAT
3. requires market capitalization
4. builds FinancialSnapshot
5. returns both the snapshot and derivation provenance

If average equity or CapEx cannot be derived safely, assembly stops with an explicit error instead of guessing.
