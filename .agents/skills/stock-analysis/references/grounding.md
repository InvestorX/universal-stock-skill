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

## Deterministic peer positioning

When `peer_positioning` is supplied, use its rank, available count, median, peer mean, and delta values directly. Do not mentally recalculate them.

Position IDs use the `peer:<subject>:position:<metric>:...` namespace and are valid deterministic metric references.

Interpret rank only according to the supplied numeric order. Rank 1 is not a general "best company" label. Delta values are subject minus comparator and do not encode desirability by themselves.

## Deterministic Peer Profile

When `peer_profile` is supplied, use the four axes separately:

- profitability
- growth
- valuation
- cash generation

Each axis contains configured/ranked metric counts and first/middle/last-third or unranked counts. Use the supplied `peer:<subject>:profile:<axis>:...` IDs for claims about these counts.

Do not add the four axes together, derive a composite score, or invent an overall peer rank. The thirds reflect metric-specific numeric ordering only.

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
