# universal-stock-skill

[English](README.md) | **日本語**

**時点整合性とEvidenceを重視した銘柄分析を、特定LLMに縛られず再利用するためのAgent Skill + Python Runtime** です。RRSIの考え方を取り入れた改善基盤も段階的に構築します。

> 現在: Runtime基盤、EDINET API / CSV Fact取込、Canonical財務Mapping・最大5年時系列、Point-in-Time対応MarketSnapshot、J-Quants V2 Market Adapter、平均自己資本・CapEx・NOPATの決定論的導出とFinancialSnapshot自動Assembly、証券コード＋as_ofから分析JSONまでのEnd-to-End Orchestrator、Evidence ID / Metric IDで検証するGrounded Analysis Report Layer、Provider-neutralなNews/適時開示/IR Evidence収集、同一as_ofの決定論的Peer比較、トヨタ7203の実在企業Regression Case、Portable Agent Skill化まで実装済みです。

## 全体像

銘柄分析は2つの実行モードに分けます。

~~~mermaid
flowchart TD
    U[ユーザーの銘柄分析依頼] --> S[stock-analysis Skill]
    S --> H[現在の親Agent]
    S --> P[決定論的Python処理]
    P --> D[財務 / 株価 / 開示 / ニュース]
    D --> P
    P --> H
    H --> R[Evidence付き分析レポート]

    S -. Standalone実行時のみ .-> RT[Universal Skill Runtime]
    RT --> A[LLM Provider Adapter]
    A --> M[明示設定されたモデル]
~~~

通常のAgent Skill利用では、**今このSkillを実行している親Agent自身を推論エンジンとして使います**。

- Codex上ならCodex
- Claude Code上ならClaude
- Antigravity CLI上なら現在のAntigravity Agent
- Hermes Agent上ならHermes

したがって、Skillとして使うだけなら別のLLM endpoint、model名、LLM API keyを設定する必要はありません。

Python standalone runtimeのProvider Adapterは、複数モデルBenchmark、Batch実行、RRSI評価など、明示的に外部モデルを切り替えたい用途だけで使います。

## 設計原則

- **Host-Agent First**: 推論は親Agentへ委譲する
- **LLM非依存**: Portable Skillへベンダー固有APIを埋め込まない
- **計算はPython**: 財務計算、時点判定、Parser、Validationは決定論的に処理する
- **Point-in-Time**: as_of より後に公開された情報を利用しない
- **Evidence First**: 重要な事実は出典と結び付ける
- **Cross-Model評価**: 特定モデルだけに最適化されたSkillを避ける
- **Reviewable Evolution**: RRSI候補は隔離・評価してGitレビュー経由で昇格する

## Portable Agent Skill

正本は次です。

~~~text
.agents/skills/stock-analysis/
├── SKILL.md
├── skill.yaml
├── references/
│   └── execution-modes.md
└── agents/
    └── openai.yaml
~~~

SKILL.md はOpen Agent Skills系の形式に合わせ、name / description のYAML frontmatterを持ちます。

Codex、Claude Code、Antigravity CLI、Hermes Agentへの導入は [docs/installation.ja.md](docs/installation.ja.md) を参照してください。

## RRSIによる改善

~~~mermaid
flowchart TD
    P[現在のProduction Skill] --> A[失敗分析]
    A --> C[Candidate生成]
    C --> B[Point-in-Time Benchmark]
    B --> X[Cross-Model評価]
    X --> K[Critic / Leakage Check]
    K -->|棄却| C
    K -->|採用| PR[Git Branch / Pull Request]
    PR --> H[人間レビュー]
    H -->|承認| P
~~~

Production Skillを実行中に直接自己書換えさせず、候補を分離して評価します。

## EDINET

現在できること:

- 日付指定の提出書類一覧取得
- docID 指定の書類取得
- EDINET提出日時のEvidence化
- XBRL変換CSV ZIPの展開
- 公式9列フォーマットのFact化
- UTF-16LE / タブ区切り読込
- Decimalへの数値正規化
- EDINETのハイフン値を明示的な0として処理
- 要素ID / コンテキストID等による決定論的Fact検索
- J-GAAP / IFRS / US-GAAPの標準TaxonomyからCanonical財務指標へのMapping
- 当期・連結・contextを考慮した決定論的Candidate選択
- 同順位Factの値衝突検出
- Mock通信による自動テスト

企業独自拡張element IDの限定Fallback、有報Resolver、最大5年のCanonical時系列化・前年比/CAGR、CanonicalFinancialSetからFinancialSnapshotへのBridgeまで実装しました。次の中心課題は、実在有報でのMapping検証、平均自己資本・CapEx等の自動導出、株価Data Sourceとの結合、実データEnd-to-End分析です。

## ドキュメント

日本語ドキュメント一覧は [docs/README.ja.md](docs/README.ja.md) にあります。

## 開発

Python 3.11以上。

~~~bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
pytest
~~~

Skill形式を検証:

~~~bash
python scripts/validate_skill.py
~~~

各Agentへ導入:

~~~bash
python scripts/install_agent_skill.py --agent all --scope user
~~~

合成データで財務計算:

~~~bash
python scripts/run_analysis.py 7203 --demo
~~~
