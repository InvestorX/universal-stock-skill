# 決定論的な財務派生値

[English](financial-derivations.md) | **日本語**

## 目的

FinancialSnapshotに残っている入力値を、LLMへ会計値の推定をさせずCanonical財務データから決定論的に作ります。

~~~mermaid
flowchart LR
    C[Canonical当期Fact] --> D[Derivation Layer]
    S[Canonical時系列] --> D
    M[MarketSnapshot] --> A[Snapshot Assembler]
    D --> A
    A --> F[FinancialSnapshot]
    F --> K[PER / PBR / ROE / FCF Yield / optional ROIC]
~~~

## 平均自己資本

第一選択は、有報に記載された公式ROEの分母を逆算する方法です。

~~~text
average_equity = net_income / official_roe
~~~

これにより、J-GAAPの純資産を自己資本として勝手に扱うことを避けます。

ROEの正規化は保守的に行います。

- 0〜1はdecimal ratioとして扱う
- 1を超える値はpercent系unitが明示されている場合のみ100で割る
- unitなしで10などの曖昧な値は採用しない

公式ROEがない場合は、現在のCanonical Mappingが親会社所有者帰属持分を優先するIFRS / US-GAAPについてのみ、当期と前期のnet_assetsから2時点平均を許可します。

J-GAAPのnet_assetsは平均自己資本へ自動代入しません。

## CapEx

CapExは次の順序で導出します。

1. 有形・無形固定資産の取得支出をまとめたFact
2. なければPPE取得支出と無形固定資産取得支出の利用可能なFactを合算

CF上の支出が負数・正数のどちらで記録されても、FinancialSnapshotへは正のCapExとして渡します。

J-GAAPの標準CF Taxonomyと、選択したIFRS / IFRS-full取得要素をサポートします。

## NOPAT

次の3項目が揃った場合だけ計算します。

- operating income
- profit before tax
- income taxes

~~~text
effective_tax_rate = income_taxes / profit_before_tax
NOPAT = operating_income × (1 - effective_tax_rate)
~~~

次の場合は計算しません。

- 税引前利益が0以下
- 法人税等が負
- 算出税率が0〜1の範囲外

税効果が特殊な年度から無理に通常税率を作ることを避けます。

## 平均投下資本

平均投下資本は今回も自動導出しません。

借入金・社債だけを部分的に拾って「投下資本」と呼ぶとROICを誤らせるためです。会計基準をまたいだ有利子負債とリース負債のCoverageを検証するまでは、ROICをoptionalのまま維持します。

## FinancialSnapshot Assembler

~~~python
result = assemble_financial_snapshot(
    current=canonical_bundle.current,
    series=canonical_bundle.series,
    market=market_snapshot,
)
~~~

Assemblerは次を行います。

1. 有報側の必須Canonical指標を確認
2. 平均自己資本・CapEx・optional NOPATを自動導出
3. 時価総額の存在を確認
4. FinancialSnapshotを生成
5. SnapshotとDerivation methodの両方を返す

平均自己資本またはCapExを安全に導出できない場合は、推測せず明示的なErrorで停止します。
