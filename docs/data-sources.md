# Data source architecture

[日本語](data-sources.ja.md)

Market-data providers are adapters, independent from the reasoning agent.

## Internal interfaces

- FinancialDataSource
- DisclosureDataSource
- PriceDataSource

Evidence-bearing data should include enough metadata to enforce point-in-time analysis:

- stable source identifier
- source type
- publication timestamp
- retrieval timestamp
- URL when available

## Japanese disclosure sources

### EDINET

EDINET is the primary statutory filing and XBRL-backed source for Japanese listed companies. API credentials remain outside the portable Skill definition.

Implemented foundation:

- document-list API
- document download
- submission timestamp to evidence metadata
- XBRL-to-CSV ZIP parsing
- official nine-column fact representation
- deterministic FactSet queries

### TDnet

TDnet is intended for timely disclosure data. Access and licensing can differ by installation, so the runtime must not assume availability.

## Point-in-time rule

~~~mermaid
flowchart TD
    F[Retrieved source] --> C{published_at <= analysis.as_of?}
    C -->|Yes| A[Eligible evidence]
    C -->|No| R[Reject as future information]
~~~

The decision belongs in deterministic runtime code, not only in a prompt.
