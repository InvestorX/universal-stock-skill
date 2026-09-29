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
