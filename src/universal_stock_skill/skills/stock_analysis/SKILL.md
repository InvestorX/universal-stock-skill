# Stock Analysis Skill

## Objective

Produce a source-grounded, point-in-time stock analysis that remains useful across different LLM providers.

## Principles

1. Never use information published after the requested `as_of` timestamp.
2. Never ask the LLM to perform authoritative financial calculations when Python can do them.
3. Distinguish reported facts, calculated metrics, assumptions and interpretation.
4. Attach evidence to material factual claims.
5. State uncertainty explicitly when evidence is incomplete.
6. Do not treat future share-price movement as the sole measure of analysis quality.

## Default workflow

1. Resolve company / security identity.
2. Load point-in-time company and market data.
3. Inspect revenue, profit and margin trends.
4. Inspect balance-sheet quality and cash flow.
5. Calculate deterministic valuation metrics.
6. Compare peers on a consistent date basis.
7. Identify growth drivers and material risks.
8. Build scenarios using explicit assumptions.
9. Produce a structured evidence-backed report.
10. Run a consistency and unsupported-claim check.

## Output sections

- Snapshot
- Earnings trend
- Profitability
- Financial position
- Cash flow
- Valuation
- Peer comparison
- Growth drivers
- Risks
- Scenarios
- Evidence
