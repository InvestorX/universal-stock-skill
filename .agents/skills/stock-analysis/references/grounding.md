# Grounded report contract

Use this reference when producing the final analysis from a deterministic stock-analysis bundle.

## IDs

Treat IDs supplied by the runtime as immutable references.

Typical IDs:

- edinet:<doc_id>
- market:<provider>:<observed_at>
- metric:<metric_name>
- trend:<canonical_metric>
- derivation:<derived_input>

Do not invent an ID that is not present in the supplied context.

## Claim classes

- fact: directly reported or observed value
- calculation: deterministic metric or trend
- interpretation: analytical reading of supplied facts
- assumption: explicit scenario input

Every material fact or calculation must identify its supporting evidence ID or deterministic metric/trend/derivation ID.

## Structured peer sections

When peer metrics are supplied, prefer structured `peer_analysis` subsections for profitability, valuation, growth, cash flow, and competitive position.

Every populated subsection must list `claim_ids` that exist in the report. Every linked claim must cite at least one supplied `peer:` metric ID or `peer:` evidence ID.

Do not attach a subject-only claim to a peer section merely because its prose mentions competitors.

## Missing source classes

If peer, news, guidance, or catalyst evidence was not supplied, do not fill those sections from model memory.

Say that evidence is unavailable or leave the section empty.

## Deterministic values

Do not silently recompute supplied metrics.

If a supplied value appears inconsistent, report the inconsistency and preserve the deterministic value rather than substituting a different mental calculation.
