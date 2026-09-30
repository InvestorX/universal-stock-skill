# Analysis report layer

[日本語](analysis-report-layer.ja.md)

## Goal

Convert the deterministic StockAnalysisDataBundle into an LLM-readable analysis context while preventing the model from inventing evidence or changing authoritative calculations.

~~~mermaid
flowchart LR
    B[StockAnalysisDataBundle]
    --> C[AnalysisContext]
    C --> L[Host Agent or LLM Provider]
    L --> R[Structured StockAnalysisReport]
    R --> G[Grounding Validator]
    C --> G
    G --> O[Evidence-grounded Report]
~~~

## AnalysisContext

The context separates four things:

- authoritative facts
- deterministic metrics
- deterministic trends / derivations
- limitations

It also exposes stable evidence IDs.

Examples:

~~~text
edinet:S100XXXX
market:jquants:v2:2026-09-29T15:30:00+09:00
metric:per
metric:roe
trend:revenue
derivation:average_equity
~~~

The model may refer to these IDs, but it may not create new IDs.

## Claim types

Structured claims are classified as:

- fact
- calculation
- interpretation
- assumption

Fact and calculation claims must reference at least one known evidence ID or deterministic metric ID.

Interpretation is allowed to express judgment from the supplied facts, but it must not smuggle in new factual assertions.

Scenario assumptions must be explicitly labelled as assumptions rather than forecasts presented as facts.

## Evidence reconstruction

The LLM does not own final evidence metadata.

Even if the model returns an evidence object, the grounding layer discards it and reconstructs the final evidence list from the trusted AnalysisContext.

Therefore a model cannot add a fabricated EDINET document, URL, publication date, or market source to the final report merely by emitting JSON.

## Missing evidence

The current deterministic bundle contains:

- EDINET filing data
- J-Quants market snapshot
- deterministic calculations and trends

It does not yet automatically contain:

- peer-company data
- news
- management guidance
- qualitative catalyst evidence

The report must not invent those sections. It should leave unsupported conclusions empty or state the limitation.

## Structured peer analysis

When peer metrics are present, the final report can use `peer_analysis` in addition to the backward-compatible free-form `peer_comparison` text.

`peer_analysis` has grounded subsections for:

- profitability
- valuation
- growth
- cash flow
- competitive position

Each populated subsection contains text plus one or more `claim_ids`. Those IDs must point to claims in the report, and every linked claim must reference at least one `peer:` metric ID or `peer:` evidence ID.

~~~json
{
  "peer_analysis": {
    "profitability": {
      "text": "Subject margins and ROE are stronger in the supplied comparison.",
      "claim_ids": ["peer-operating-margin", "peer-roe"]
    },
    "valuation": {
      "text": "Conventional PER is unavailable for loss-making peers.",
      "claim_ids": ["peer-negative-per"]
    }
  }
}
~~~

Grounding rejects:

- structured peer analysis when `AnalysisContext.peer_metrics` is empty
- unknown claim IDs
- claims linked into peer sections that do not cite any `peer:` metric or evidence ID

This makes the peer narrative traceable to the same deterministic comparison rows used by the analysis context.

## Standalone runtime

StockAnalysisWorkflow now has three entry points:

~~~python
workflow.run(snapshot)       # legacy snapshot-only path
workflow.run_bundle(bundle) # preferred grounded path
workflow.run_context(ctx)   # prebuilt AnalysisContext
~~~

run_bundle() is the preferred standalone path.

The structured report is validated twice:

1. Pydantic / JSON Schema validation
2. grounding validation against AnalysisContext

## Host-agent skill execution

When the portable Agent Skill is used directly in Codex, Claude Code, Antigravity, or Hermes, the current host agent remains the reasoning engine.

The same contract applies:

- deterministic values are authoritative
- material factual claims must map to supplied evidence
- missing source classes must not be invented
- assumptions and interpretations must be labelled
