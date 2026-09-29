# universal-stock-skill

[English](README.md) | **日本語**

**LLMに依存しない銘柄分析Skill Runtime** と、RRSI（Recursive Self-Improvement）の考え方を取り入れた自動改善基盤です。

> 現在の状態: Runtime / Point-in-Time / EDINET接続基盤を実装中

## このプロジェクトの目的

銘柄分析の知識・分析手順・評価方法を、特定のLLMベンダーから切り離します。

```text
Stock Analysis Skill
        |
        v
Universal Skill Runtime
        |
   +----+-----+---------+-----------+
   |          |         |           |
 OpenAI    Claude    Gemini    Local LLM
   |          |         |           |
   +----------+---------+-----------+
              |
              v
       Pythonによる決定論的処理
              |
              v
      財務 / 株価 / 開示 / ニュース
```

LLMは「考える・解釈する・文章化する」ことに使い、計算や時点判定など、正確さを機械的に保証できる処理はPythonで行います。

## RRSIによるSkill改善

本番Skill自身を書き換えさせるのではなく、候補を隔離して評価します。

```text
現在のSkill
    |
    v
失敗分析
    |
    v
改善候補A / B / C
    |
    v
Point-in-Time Benchmark
    |
    v
複数LLMで評価
    |
    v
Critic / 漏洩チェック
    |
    v
採用Candidate
    |
    v
Git Branch / Pull Request
    |
    v
人間がレビューして本番昇格
```

## 設計原則

- **LLM非依存**: SkillにはOpenAI・Anthropic・Gemini固有の命令を書かない
- **計算はPython**: PER、PBR、CAGR、利益率、ROE、ROICなどはLLMに計算させない
- **Point-in-Time**: `as_of` より未来の情報を使用しない
- **Evidence First**: 重要な事実には出典情報を紐付ける
- **Cross-Model評価**: 特定モデルだけに最適化されたSkillを避ける
- **Reviewable Evolution**: 自動改善結果はGit/PR経由でレビュー可能にする

## ディレクトリ構成

```text
docs/
  architecture.md
  skill-spec.md
  benchmark-spec.md
  rrsi-design.md
  provider-adapters.md
  data-sources.md

src/universal_stock_skill/
  llm/                   # LLM共通インターフェース / Provider Adapter
  runtime/               # Skill実行Runtime / Tool Registry
  finance/               # 決定論的な財務計算
  benchmark/             # Point-in-Time Benchmark
  evidence/              # 出典情報 / 未来情報漏洩防止
  data/                  # EDINET等のデータソースAdapter
  analysis/              # 指標計算 -> LLM分析Workflow
  skills/stock_analysis/ # 銘柄分析Skill
  evolution/             # RRSI評価・Fitness

scripts/
tests/
```

## 銘柄分析での役割分担

### Pythonが担当

- 株価・財務データ取得
- 日付・公開時点チェック
- PER / PBR
- CAGR
- 利益率
- ROE / ROIC
- キャッシュフロー指標
- ランキング
- 比較用データ整形

### LLMが担当

- 業績変化の意味を解釈
- 成長ドライバーの整理
- リスクの抽出
- シナリオ分析
- 財務・開示・ニュース間の関係整理
- 最終レポート作成

## Point-in-Time

過去時点の銘柄分析やRRSIのBenchmarkでは、`as_of` より後に公開された資料を使用してはいけません。

```text
資料の published_at <= analysis.as_of
                    |
                 利用可能

資料の published_at > analysis.as_of
                    |
              Runtimeで拒否
```

この判定はLLMへの指示ではなく、Pythonの `PointInTimeGuard` で強制します。

## EDINET

EDINET API v2向けのクライアント基盤を実装しています。

現在できること:

- 日付を指定した提出書類一覧の取得
- `docID` を指定した書類データの取得
- EDINET提出日時をEvidenceへ変換
- API通信をMock化した自動テスト

まだ未実装:

- XBRL / CSVから財務数値を正規化して抽出
- 証券コードから必要書類を自動選択
- 訂正報告書・複数提出書類の優先順位処理
- FinancialSnapshotへの自動変換

## 開発環境

Python 3.11以上。

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
pytest
```

合成データだけで財務計算を試す場合:

```bash
python scripts/run_analysis.py 7203 --demo
```

## 現在のロードマップ

### Phase 1 — Foundation
- [x] LLM共通インターフェース
- [x] Stock Analysis Skill初期定義
- [x] Point-in-Time Benchmark設計
- [x] Cross-Model Fitness設計
- [x] RRSI改善フロー設計

### Phase 2 — Runnable Runtime
- [x] Provider Capabilityモデル
- [x] OpenAI-Compatible Adapter
- [x] Tool Registry
- [x] 財務計算モジュール
- [x] Benchmark Caseモデル
- [x] Structured Output validation
- [x] Stock Analysis Workflow基盤
- [x] Evidence / Point-in-Time Guard
- [ ] Provider-neutral Tool Calling fallback
- [ ] 実データを使ったEnd-to-End分析

### Phase 3 — Market Data
- [x] EDINET APIクライアント基盤
- [ ] EDINET XBRL / CSV財務データ抽出
- [ ] TDnet
- [ ] 株価データ
- [ ] IR資料
- [ ] ニュース

### Phase 4 — Evolution
- [ ] Candidate Proposer
- [ ] Critic
- [ ] Multi-Model Benchmark Runner
- [ ] Git Worktree isolation
- [ ] Candidate PR自動生成

詳しい設計は [docs/architecture.md](docs/architecture.md) を参照してください。
