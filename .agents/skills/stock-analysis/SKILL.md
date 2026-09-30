---
name: stock-analysis
description: Produces point-in-time, evidence-grounded stock and company analysis from filings, market data, financial metrics, and news. Use for listed-company analysis, earnings, valuation, profitability, balance sheet, cash flow, peer comparison, catalysts, risks, or scenarios. 日本株の銘柄分析、決算分析、バリュエーション、業績・財務・リスク分析にも使用する。
---

# Stock Analysis

## Execution model

Use the **current host agent** as the reasoning engine.

Do not ask the user to configure another LLM endpoint, model, or LLM API key merely to execute this skill.

- On Codex, use the current Codex session.
- On Claude Code, use the current Claude Code session.
- On Antigravity, use the current Antigravity agent.
- On Hermes, use the current Hermes agent.
- Prefer tools already available to the host agent for web/search, MCP, files, browser, and shell access.
- Use deterministic Python helpers when a calculation, date rule, parsing rule, or validation can be machine-enforced.
- Use the standalone Python LLM runtime only when the user explicitly requests controlled external model routing, cross-model benchmarking, batch execution, or RRSI evaluation.

For execution-mode details, read references/execution-modes.md only when needed.
For grounded-report ID and claim rules, read references/grounding.md when producing the final report from a deterministic bundle.

## Objective

Produce a source-grounded, point-in-time stock analysis without depending on one LLM vendor.

## Inputs

Resolve as much of the following as the task requires:

- company or security identity
- ticker / security code
- analysis as-of timestamp
- requested analysis scope
- comparison peers when relevant

If no historical as-of is requested, use the current time available to the host as the analysis cutoff.

## Non-negotiable rules

1. Never use information published after the analysis as-of timestamp.
2. Never invent evidence, filings, prices, financial values, or source metadata.
3. Do not make authoritative financial calculations in free-form reasoning when deterministic calculation is available.
4. Separate reported facts, deterministic calculations, assumptions, and interpretation.
5. Attach or identify evidence for material factual claims.
6. Treat deterministic metric / trend / derivation IDs supplied by the runtime as authoritative references; do not silently recompute them.
7. Never invent evidence IDs, source metadata, peer data, news, guidance, or catalysts that were not supplied.
8. State missing evidence and uncertainty explicitly.
9. Keep comparison dates and accounting periods consistent.

## Workflow

1. Resolve company and security identity.
2. Establish the as-of timestamp and timezone.
3. Gather only evidence available by that cutoff.
4. Prefer primary filings and company disclosures for reported financial facts.
5. Use deterministic tools or Python for financial metrics and point-in-time checks.
6. Analyze earnings and margin trends.
7. Analyze balance-sheet quality and cash flow.
8. Evaluate valuation using explicitly dated inputs.
9. Compare peers on a consistent basis when requested.
10. When peer comparison is requested, use peer data aligned to the same as-of timestamp and the same comparable accounting period end; do not assume issuer fiscal-year labels mean the same period. Prefer deterministic peer metric IDs over mental recalculation.
11. For news, timely disclosures, or company IR, preserve source_id, published_at, URL, and enough excerpt/context to support material claims.
12. Identify growth drivers, catalysts, and material risks only from supplied evidence.
13. Build scenarios with explicit assumptions rather than hidden forecasts.
14. Classify material claims as fact, calculation, interpretation, or assumption when structured output is available.
15. Produce the report and run an unsupported-claim / consistency check.

## Output

Use sections appropriate to the available evidence:

- Snapshot
- Earnings trend
- Profitability
- Financial position
- Cash flow
- Valuation
- Peer comparison
- Growth drivers / catalysts
- Risks
- Scenarios
- Evidence and limitations

For every important calculated metric, preserve the input values or enough provenance to reproduce it.

When a deterministic AnalysisContext is available:

- cite only evidence / metric / trend / derivation IDs that exist in that context
- do not replace deterministic values with mental arithmetic
- leave peer comparison, news-driven catalysts, or guidance conclusions empty when their evidence was not supplied
- keep scenario statements explicitly labelled as assumptions

When deterministic peer metrics are available, prefer the structured `peer_analysis` output contract:

- profitability
- valuation
- growth
- cash flow
- competitive position

Each populated peer subsection must reference existing structured claim IDs, and those claims must cite supplied `peer:` metric or evidence IDs. Do not create a peer subsection from unsupported prose alone.

When deterministic peer positioning is supplied, use its rank/count/median/peer-mean/delta values directly instead of recalculating them. Treat rank as metric-specific numeric ordering only, not as an overall investment score.

When a deterministic Peer Profile is supplied, report profitability, growth, valuation, and cash-generation axes separately. Use the supplied axis counts and preserve unranked metrics. Never sum the axes into a composite score or overall peer rank.

## Verification

Before finishing, verify:

- no source violates the as-of cutoff
- deterministic values were not silently recomputed differently
- important factual claims have evidence
- assumptions are labeled
- missing data is not filled with guesses
- valuation and peer inputs use compatible dates
