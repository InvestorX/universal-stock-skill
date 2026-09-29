# トヨタ 7203 Reference Case

[English](toyota-reference-case.md) | **日本語**

## 目的

トヨタ自動車（証券コード7203）を、このProject最初の**実在企業Regression Case**として追加します。

Toyota公式の2026年3月期決算要旨と2026年のIR開示から一部の値・Evidenceを固定し、CIがLive Webへ依存せずに、決定論的な財務計算、Evidence処理、Point-in-Time Guardを検証できるようにします。

~~~mermaid
flowchart LR
    T[Toyota公式IR]
    --> R[Toyota Reference Case]
    R --> F[FY2025 / FY2026固定Fact]
    R --> E[公式Qualitative Evidence]
    F --> X[Regression計算]
    E --> G[Point-in-Time EvidenceCollector]
    X --> B[Benchmark / RRSI Check]
    G --> B
~~~

## 対象期間

2026年3月期。

会計基準: IFRS。

固定した主な公式値:

| 項目 | FY2026 | FY2025 | 単位 |
|---|---:|---:|---|
| 営業収益 | 50,684,952 | 48,036,704 | 百万円 |
| 営業利益 | 3,766,216 | 4,795,586 | 百万円 |
| 税引前利益 | 5,152,996 | 6,414,590 | 百万円 |
| 親会社帰属利益 | 3,848,098 | 4,765,086 | 百万円 |
| 資産合計 | 105,522,331 | 93,601,350 | 百万円 |
| 親会社所有者帰属持分 | 39,918,854 | 35,924,826 | 百万円 |
| 営業CF | 5,472,920 | 3,696,934 | 百万円 |
| 法人所得税費用 | 1,167,234 | 1,624,835 | 百万円 |
| 基本EPS | 295.25 | 359.56 | 円/株 |
| BPS | 3,062.82 | 2,753.09 | 円/株 |
| ROE | 10.1% | 13.6% | % |
| 営業利益率 | 7.4% | 10.0% | % |

Primary Source:

- Toyota Motor Corporation FY2026 Financial Summary, 2026-05-08
- https://global.toyota/pages/global_toyota/ir/financial-results/2026_4q_summary_en.pdf

## Regression Check

Testでは公式表示値をコピーして終わりにせず、Pythonで次を再計算します。

- FY2026営業利益率
- 売上高前年比
- 営業利益前年比
- 親会社帰属利益前年比
- 親会社所有者帰属持分の2時点平均
- 2時点平均持分と親会社帰属利益からROE
- 実効税率
- NOPAT

Toyota公式が公表している比率・前年比について、丸め後の値が一致することを検証します。

これにより、Synthetic Dataだけではなく**実在IFRS企業で財務計算ロジックをRegression Test**できます。

## Qualitative Evidence

Case cutoffまでに公表されたToyota公式IRも含めます。

1. 2026年3月期決算発表（2026-05-08）
2. 2027年3月期 第1四半期決算発表（2026-08-04）
3. 自己株式取得・自己株式消却の開示（2026-08-04）

自己株取得開示では、最大5億株・最大1兆円、取得期間2026-08-05〜2027-08-04、自己株式2億株の消却が示されています。

Source:

- https://global.toyota/pages/global_toyota/ir/stock/share/commonstock_20260804_en.pdf

これらも通常Runtimeと同じEvidenceCollector / PointInTimeGuardを通します。

## 株価の扱い

Reference Caseでは**株価を固定しません**。

PER/PBRなどPoint-in-Time Valuationに使う株価・時価総額は、指定as_ofに対してMarketDataSource / J-Quantsから取得します。

任意の日の株価を恒久的な企業FactとしてFixtureへ固定しないためです。

## Fixture確認

~~~bash
python scripts/inspect_toyota_reference.py
~~~

でReference Case全体をJSON表示できます。
