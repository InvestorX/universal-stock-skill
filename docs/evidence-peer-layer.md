# Qualitative evidence and peer-comparison layer

[日本語](evidence-peer-layer.ja.md)

## Goal

Extend deterministic stock analysis with peer comparison and qualitative evidence without binding the project to one news vendor or disclosure API.

~~~mermaid
flowchart LR
    H[Host Agent / Provider]
    --> E[EvidenceItem]
    E --> C[EvidenceCollector]
    C --> G[Point-in-Time Guard + Dedup]

    P1[Subject Bundle] --> PC[Peer Comparison]
    P2[Peer Bundle] --> PC
    P3[Peer Bundle] --> PC

    G --> A[AnalysisContext]
    PC --> A
    A --> L[Host Agent / LLM]
    L --> R[Grounded Report]
~~~

## EvidenceItem

Qualitative evidence wraps a trusted SourceRecord together with:

- symbol
- excerpt
- tags

SourceRecord continues to carry:

- source_id
- source_type
- title
- published_at
- retrieved_at
- optional effective_at
- URL
- content hash
- metadata

Supported source types already include:

- filing
- timely_disclosure
- price
- news
- company_ir
- other

This means a host agent can use its own browser/search/MCP tools and convert the result into EvidenceItem without configuring a second LLM or a specific news endpoint.

## EvidenceCollector

EvidenceCollector accepts one or more EvidenceSource implementations.

Every result is checked for:

- symbol consistency
- published_at <= as_of
- timezone-aware timestamps

Results are deduplicated by content_hash when available, otherwise by source_id.

When duplicate content exists, the latest published record is retained. Final results are sorted newest first.

A provider returning future evidence is treated as an error rather than silently accepted.

## Peer comparison

Peer comparison uses already-built StockAnalysisDataBundle objects.

All bundles must:

- have unique symbols
- use the exact same requested_as_of

The comparison exposes deterministic IDs such as:

~~~text
peer:7203:per
peer:6758:per
peer:6758:pbr
peer:6758:roe
peer:6758:operating_margin
peer:6758:free_cash_flow_yield
peer:6758:revenue_yoy
~~~

The LLM therefore does not need to recalculate comparison metrics.

Peer filing and market provenance is also added to AnalysisContext using namespaced evidence IDs such as:

~~~text
peer:6758:edinet:S100XXXX
peer:6758:market:jquants:v2:...
~~~

## Deterministic relative positioning

`PeerComparisonSet` can be converted into a deterministic `PeerPositioningSet`. This prevents the model from calculating ranks, medians, or peer averages in free-form reasoning.

The positioning layer currently covers:

- PER: ascending numeric order
- PBR: ascending numeric order
- ROE: descending numeric order
- operating margin: descending numeric order
- free-cash-flow yield: descending numeric order
- revenue YoY: descending numeric order

For each metric it records:

- subject value
- rank and available-company count
- comparison-set median, including the subject
- delta from that median
- peer-only mean, excluding the subject
- delta from that peer-only mean

Ranks are emitted only when at least two comparable values exist. Missing values are excluded. Exact ties share the same competition rank.

Stable metric IDs are added to `peer_metrics`, for example:

~~~text
peer:7203:position:operating_margin:rank
peer:7203:position:operating_margin:available_count
peer:7203:position:operating_margin:comparison_median
peer:7203:position:operating_margin:delta_to_median
peer:7203:position:operating_margin:peer_mean
peer:7203:position:operating_margin:delta_to_peer_mean
~~~

All deltas are `subject - comparator`. Their sign is a numerical difference only. Rank 1 means first under the documented numeric ordering for that metric; it is not a general investment score or a claim that the company is universally "best."

## Deterministic four-axis Peer Profile

`PeerPositioningSet` is also aggregated into a deterministic `PeerProfileSet`. The profile intentionally does **not** create a composite score or overall peer rank.

The four axes are:

- profitability: operating margin, ROE
- growth: revenue YoY
- valuation: PER, PBR
- cash generation: free-cash-flow yield

For each metric, the existing deterministic rank is normalized within the number of comparable values:

~~~text
rank_fraction = (rank - 1) / (available_count - 1)
~~~

The metric is then classified as:

- `first_third`: rank_fraction < 1/3
- `middle_third`: 1/3 <= rank_fraction <= 2/3
- `last_third`: rank_fraction > 2/3
- `unranked`: no deterministic rank is available

Each axis reports only counts:

- configured_metric_count
- ranked_metric_count
- first_third_count
- middle_third_count
- last_third_count
- unranked_count

Stable grounding IDs include:

~~~text
peer:7203:profile:profitability:configured_metric_count
peer:7203:profile:profitability:ranked_metric_count
peer:7203:profile:profitability:first_third_count
peer:7203:profile:valuation:unranked_count
peer:7203:profile:cash_generation:ranked_metric_count
~~~

The profile preserves the metric-specific numeric orders already defined by peer positioning. A first-third count is therefore a statement about position under those documented orders, not a general quality score. Axes must remain separate; callers and models must not sum them into an overall score or overall company ranking.

## AnalysisContext enrichment

build_analysis_context() accepts optional:

~~~python
context = build_analysis_context(
    subject_bundle,
    evidence_items=evidence_items,
    peer_bundles=peer_bundles,
)
~~~

When supplied:

- qualitative evidence is added to authoritative_facts
- trusted EvidenceRef records are added to the grounding set
- peer comparison is added to authoritative_facts
- peer metrics become valid grounding metric IDs
- limitations are reduced only for evidence classes that are actually present

If news is absent, the context still says news evidence is unavailable. Supplying peer data does not imply that news, company IR, or catalyst evidence exists.

## Generic subject + peer orchestration

Production callers can now build the subject and all peers from one shared point-in-time cutoff:

~~~python
peer = PeerAnalysisOrchestrator(stock_orchestrator)
result = await peer.analyze(
    "7203",
    peer_symbols=["7267", "7201"],
    as_of=as_of,
    years=5,
)
context = result.build_context()
~~~

The orchestrator normalizes symbols, rejects duplicates before provider I/O, runs every company with the exact same `as_of`, preserves peer order, and produces a deterministic `PeerComparisonSet`.

CLI:

~~~bash
python scripts/analyze_peers.py 7203 \
  --peers 7267 7201 \
  --as-of 2026-09-29T15:30:00+09:00
~~~

PER is now unavailable when EPS is zero or negative in the production metric pipeline, preventing a negative multiple from being interpreted as a conventional low PER.

## Provider strategy

The core runtime intentionally does not require one specific news API.

Concrete providers can be added later for:

- TDnet / timely disclosures
- company IR feeds
- licensed news providers
- host-agent web research
- internal research databases

All providers must emit the same EvidenceItem contract and pass the same point-in-time guard.
