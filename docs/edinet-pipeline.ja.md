# EDINET分析Pipeline

[English](edinet-pipeline.md) | **日本語**

## 現在の経路

~~~mermaid
flowchart LR
    S[証券コード] --> R[AnnualFilingResolver]
    R --> D[選択されたEDINET書類]
    D --> Z[CSV ZIP取得]
    Z --> P[EDINETCsvArchive]
    P --> F[EDINETCsvFact]
    F --> C[CanonicalFinancialMapper]
    C --> CF[CanonicalFinancialSet]
    CF --> B[FinancialSnapshot Bridge]
    B --> FS[FinancialSnapshot]
    FS --> M[決定論的財務指標]
    M --> A[stock-analysis Skill]
~~~

## 有報選択

有価証券報告書の選択もPoint-in-Timeを守ります。

Resolverは次を行います。

- 4文字の証券コードをEDINETの5文字形式へ正規化
- 指定as-ofまでに公開済みの年次有報だけを対象
- 最新事業年度を選択
- 訂正報告書のparent関係を追跡
- cutoffまでに利用可能な最新訂正版を選択
- cutoffより未来の訂正報告書は利用しない

元の有報と最終的に選択した書類の両方を保持します。

## CanonicalからFinancialSnapshotへのBridge

現在EDINETからCanonical経由で供給するFinancialSnapshot必須値:

- revenue
- operating income
- net income
- EPS
- BPS
- operating cash flow

次の値は別の決定論的Data Sourceまたは派生計算から供給します。

- 株価
- 時価総額
- 平均自己資本
- CapEx
- NOPAT
- 平均投下資本

この分離は意図的です。株価を有報から捏造したり、期首・期末が必要な平均残高を単一時点値から代用したりしません。

## 実書類のMapping確認

EDINET API keyがある環境では:

~~~bash
export EDINET_API_KEY=...
python scripts/inspect_edinet_document.py S100XXXX
~~~

Windows PowerShell:

~~~powershell
$env:EDINET_API_KEY="..."
python scripts/inspect_edinet_document.py S100XXXX
~~~

このコマンドはEDINETのdocument type 5を取得し、XBRL変換CSVをparseしてCanonical Mapping結果とmissing項目をJSON表示します。

LLMは呼び出しません。
