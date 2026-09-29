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

## Provider strategy

The core runtime intentionally does not require one specific news API.

Concrete providers can be added later for:

- TDnet / timely disclosures
- company IR feeds
- licensed news providers
- host-agent web research
- internal research databases

All providers must emit the same EvidenceItem contract and pass the same point-in-time guard.
