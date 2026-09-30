# データソース設計

[English](data-sources.md) | **日本語**

市場データProviderは、推論を担当するAgentとは独立したAdapterとして扱います。

## 内部Interface

- FinancialDataSource
- DisclosureDataSource
- PriceDataSource

Evidenceを伴うデータにはPoint-in-Time判定に必要なメタデータを持たせます。

- 安定したsource ID
- source type
- 公開日時
- 取得日時
- 利用可能ならURL

## 日本の開示データ

### EDINET

EDINETを法定開示・XBRLベース財務データの主要ソースとして扱います。API key等の資格情報はPortable Skillへ埋め込まず、Data Source Adapter側で管理します。

実装済み基盤:

- 書類一覧API
- 書類取得
- 提出日時からEvidence metadataへの変換
- XBRL変換CSV ZIP parser
- 公式9列Fact表現
- FactSetによる決定論的検索

### TDnet

適時開示取得に利用する予定です。契約・利用条件は環境によって異なるため、RuntimeはTDnetが必ず使えるとは仮定しません。

## Point-in-Timeルール

~~~mermaid
flowchart TD
    F[取得したSource] --> C{published_at <= analysis.as_of ?}
    C -->|Yes| A[利用可能なEvidence]
    C -->|No| R[未来情報として拒否]
~~~

この判定はLLMへのお願いではなく、決定論的Runtime codeで強制します。
