# Benchmark仕様

[English](benchmark-spec.md) | **日本語**

Benchmarkは「その後株価が上がったか」ではなく、**その時点で利用可能だった情報からどれだけ正確で根拠ある分析を行えたか**を測ります。

## Point-in-Time Case

各Caseはtimezone-awareなas_ofを持ちます。as_ofより後に公開された情報は利用不可です。

~~~yaml
symbol: "7203"
as_of: "2025-02-10T15:00:00+09:00"
task: "Analyze earnings quality and valuation."
~~~

## 初期Score

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

## Cross-Model Robustness

Candidateは複数のmodel familyで評価します。

~~~text
fitness = mean(score_by_model)
          - robustness_penalty * stdev(score_by_model)
          - cost_penalty
~~~

単一モデルでの最高点が少し低くても、複数モデルで安定するCandidateを高く評価できる形にします。

## Hard Failure

次の場合は無効Runです。

- as_ofより後の情報を利用
- Evidenceやsource metadataを捏造
- 決定論的期待値を許容誤差外へ変更
- Benchmark Case固有のhard-code
