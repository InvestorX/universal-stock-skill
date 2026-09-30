# Benchmark specification

[日本語](benchmark-spec.ja.md)

The benchmark measures analysis quality, not whether a stock later went up.

## Point-in-time case

Every case must include a timezone-aware as_of timestamp. Data published after that timestamp is unavailable to the candidate.

~~~yaml
symbol: "7203"
as_of: "2025-02-10T15:00:00+09:00"
task: "Analyze earnings quality and valuation."
~~~

## Initial score dimensions

| Dimension | Weight |
|---|---:|
| Data accuracy | 0.20 |
| Calculation accuracy | 0.15 |
| Evidence grounding | 0.15 |
| Financial analysis | 0.15 |
| Valuation reasoning | 0.10 |
| Risk analysis | 0.10 |
| Scenario analysis | 0.10 |
| Internal consistency | 0.05 |

## Cross-model robustness

A candidate should be evaluated on more than one model family.

~~~text
fitness = mean(score_by_model)
          - robustness_penalty * stdev(score_by_model)
          - cost_penalty
~~~

A candidate with a slightly lower peak score but much better model portability may therefore win.

## Hard failures

A run is invalid if it:

- uses information published after as_of
- fabricates evidence or source metadata
- changes a deterministic expected value outside tolerance
- includes benchmark-case-specific hard-coded behavior


## Real-company reference cases

Synthetic benchmark cases remain useful for edge conditions, but deterministic finance code also needs regression checks against real issuer disclosures.

The first frozen real-company case is:

- `toyota-7203-fy2026`
- Toyota Motor Corporation
- IFRS
- FY2025 / FY2026 official financial-summary values
- official 2026 IR evidence
- point-in-time cutoff: 2026-09-29T23:59:00+09:00

See [Toyota 7203 reference case](toyota-reference-case.md).

Reference cases are **fixtures, not candidate-specific hints**. Candidate prompts or workflows must not branch on a case ID, company name, or security code to improve a benchmark score.
