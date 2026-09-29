# Grounded Report契約

決定論的Stock Analysis Bundleから最終分析を作る場合に使用します。

## ID

Runtimeが供給したIDを変更不可の参照として扱います。

代表例:

- edinet:<doc_id>
- market:<provider>:<observed_at>
- metric:<metric_name>
- trend:<canonical_metric>
- derivation:<derived_input>

Contextに存在しないIDを新しく作ってはいけません。

## Claim分類

- fact: 開示・観測された事実値
- calculation: 決定論的Metric / Trend
- interpretation: 与えられたFactの分析的解釈
- assumption: Scenarioの明示的仮定

重要なfact / calculationは、Evidence IDまたはmetric / trend / derivation IDへ紐付けます。

## Sourceがない場合

Peer、News、Guidance、CatalystのEvidenceが渡されていない場合、モデル知識で埋めてはいけません。

Evidence不足を明示するか空欄にします。

## 決定論的値

供給済みMetricを暗算で再計算して置き換えません。

不整合が疑われる場合は、値を勝手に修正せず不整合として報告します。
