# EDINET Canonical財務Mapping

[English](edinet-canonical-mapping.md) | **日本語**

## 目的

EDINETのXBRL変換CSV Factを、LLMに「この行が売上高っぽい」と推測させず、安定した共通財務指標へ変換します。

~~~mermaid
flowchart LR
    CSV[EDINET CSV Fact] --> M[Canonical Mapper]
    M --> R[Taxonomy完全一致Rule]
    R --> C[Canonical Financial Fact]
    C --> A[銘柄分析 / 財務指標計算]
~~~

まず既知の標準Taxonomy element IDを完全一致でMappingします。標準Mappingで取れなかった場合だけ、revenueとoperating_incomeに限定して企業独自拡張IDのFallbackを許可します。

## Core指標

初期対象:

- revenue
- operating_income
- profit_before_tax
- net_income
- total_assets
- net_assets
- eps
- diluted_eps
- bps
- roe_official
- equity_ratio_official
- cf_operating
- cf_investing
- cf_financing
- cash

## 会計基準

Canonical Factには元の会計基準も保持します。

- J-GAAP
- IFRS
- US-GAAP
- unknown

下流では共通名で扱えますが、元のelement ID、項目名、context、unit、CSV位置を残すため、どの値から変換されたか追跡できます。

## Candidate選択

完全一致したTaxonomy候補をPythonで決定論的にscoreします。

優先順位:

1. Mapping Ruleのpriority
2. 当期
3. AUTO時は連結
4. Memberではないcontext
5. 期待する期間 / 時点
6. CurrentYear context

同一優先度の候補で値が食い違う場合は、勝手に選ばず CanonicalMappingConflict を発生させます。

## 売上高の意味差

revenue は業種をまたいで完全に同一概念とは限りません。

たとえば金融機関では、一般事業会社の売上高に相当する入口指標として経常収益が使われることがあります。こうしたMappingにはsemantic noteを付け、Peer比較で同一概念と誤認しないようにします。

## Extension Fallback

Fallbackは意図的に狭くしています。

- 標準Taxonomyの完全一致で取れなかった場合だけ実行
- 有価証券報告書の企業拡張namespaceだけを対象
- 現在はrevenue / operating_income / net_incomeを対象
- SummaryOfBusinessResults / KeyFinancialData系のlocal nameを要求
- 指標ごとにIntersegment / Cost / Gain / Loss / Proceeds / Ordinary / BeforeTax / Segment / PerShare / Ratio等を除外
- 結果にmatch_type=extension_fallbackを保持
- 元element IDを必ず保持

次は実在企業の有報でFallback ruleを検証し、CanonicalFinancialSetからFinancialSnapshotへの変換へ接続します。


## 会計基準の自動判定

企業独自拡張element名には、必ずしもIFRS等の文字列が含まれません。

Extension Fallback時は有報内の当期Fact全体から会計基準を判定します。

1. 当期element IDにUSGAAP / us-gaapがあればUS-GAAP
2. 当期element IDにIFRS / ifrs-fullがあればIFRS
3. 当期Factが存在し上記に該当しなければJ-GAAP
4. 当期情報自体がなければunknown

標準Taxonomyの完全一致Mappingでは、Rule側で明示した会計基準をそのまま保持します。


## 時系列Series

EDINETの有価証券報告書CSVには、当期だけでなく前期以前の再掲値が含まれることがあります。

Mapperではcontextをyear offsetへ正規化します。

| EDINET context | year_offset |
|---|---:|
| CurrentYear... | 0 |
| Prior1Year... | 1 |
| Prior2Year... | 2 |
| PriorNYear... | N |

`resolve_series(..., years=5)` で、LLMに期間合わせをさせず `CanonicalFinancialSeries` を生成できます。

このSeriesからPythonで次を計算します。

- 前年比
- 利用可能な最古の正の基準値からCAGR
- 汎用的な2時点平均

基準値が0以下の場合は、赤字→黒字などに誤解を招く成長率を出さず `None` とします。

2時点平均は汎用関数として提供しますが、`net_assets` をそのままROE用の自己資本へ自動代入はしません。JP GAAPの株主資本とIFRSの親会社所有者帰属持分は厳密には同一概念ではないためです。
