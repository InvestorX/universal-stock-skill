# RRSIベース改善設計

[English](rrsi-design.md) | **日本語**

再帰的改善の考え方を利用しつつ、Production変更は必ずレビュー可能な状態に保ちます。

## Component

- **Analyst**: Benchmark失敗とTraceを分析
- **Proposer**: 小さな改善Candidateを生成
- **Critic**: 情報漏洩、Benchmark暗記、一般化しない変更を棄却
- **Evaluator**: Point-in-Time / Cross-Model Benchmarkを実行
- **Fitness**: 品質、Model間安定性、Costを統合
- **Promoter**: 採用CandidateのPRを作る

## 初期の編集可能範囲

- Prompt / Skill instruction
- Workflow順序
- Evidence rule
- Tool選択policy
- Structured Output Schema

Runtime codeまで自動変更する段階では、より厳しいTest Gateを追加します。

## Safety Boundary

- mainやdeploy済みSkillを直接書換えない
- Candidateごとにbranch/worktreeで隔離
- held-out Caseを必須化
- experiment metadataを完全保存
- Production昇格前に人間レビュー必須
