# アーキテクチャ

[English](architecture.md) | **日本語**

## 目的

universal-stock-skill は、銘柄分析の手順を特定のLLMベンダーから切り離します。実行系は2つに分けます。

~~~mermaid
flowchart LR
    subgraph AgentSkill["Agent Skill系 - 通常はこちら"]
        U[ユーザー] --> S[stock-analysis SKILL.md]
        S --> H[親Agentの推論]
        S --> P[決定論的Python]
        P --> E[Evidence / 市場データ]
        E --> P
        P --> H
        H --> O[構造化された銘柄分析]
    end

    subgraph Standalone["Standalone Runtime - 任意"]
        C[CLI / Benchmark / RRSI] --> RT[SkillRuntime]
        RT --> PA[Provider Adapter]
        PA --> LM[明示設定したLLM]
        RT --> P2[決定論的Python]
    end
~~~

## Agent Skill系

Codex、Claude Code、Antigravity CLI、Hermes AgentへSkillとして導入する場合の標準モードです。

親Agentはすでにモデル選択、認証、推論、固有Toolを持っています。そのためSkill実行のためだけに、別のLLM endpointやAPI keyを要求しません。

親Agentが解釈・統合・文章化を担当し、Pythonは計算、Parser、時点判定など決定論的な処理を担当します。必要な情報取得には親Agentが持つWeb、Browser、MCP、File、Shell等を優先利用します。

## Standalone Runtime系

LLMをプログラムから明示的に切り替える必要がある用途で使います。

- Cross-Model Benchmark
- RRSI Candidate評価
- Batch処理
- Provider比較
- アプリケーション組込み

このモードでのみProvider Adapterやendpoint設定が必要です。

## レイヤ

1. Portable Skill — Agent Skills互換のSKILL.mdと参照資料
2. 決定論的Domain層 — finance、evidence、Point-in-Time、EDINET Fact
3. Host Agent実行 — 通常の推論経路
4. Standalone Runtime — 任意のプログラム実行
5. Provider Adapter — Standalone時のモデルAPI差異吸収
6. Evolution — RRSI候補生成・評価・昇格

## RRSIフロー

~~~mermaid
flowchart TD
    P[Production Skill] --> A[失敗分析]
    A --> C[Candidate生成]
    C --> B[Point-in-Time Benchmark]
    B --> X[Cross-Model評価]
    X --> K[Critic / Leakage Check]
    K -->|棄却| C
    K -->|採用| PR[Branch / Pull Request]
    PR --> HR[人間レビュー]
    HR -->|昇格| P
~~~

Production Skillをその場で直接自己書換えさせません。
