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
- 現在はrevenueとoperating_incomeのみ
- SummaryOfBusinessResults / KeyFinancialData系のlocal nameを要求
- Intersegment / Segment / Cost / Expense / PerShare / Ratio等を除外
- 結果にmatch_type=extension_fallbackを保持
- 元element IDを必ず保持

次は実在企業の有報でFallback ruleを検証し、CanonicalFinancialSetからFinancialSnapshotへの変換へ接続します。
