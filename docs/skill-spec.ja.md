# Skill仕様

[English](skill-spec.md) | **日本語**

## Portable形式

配布用Skillの正本は次に置きます。

~~~text
.agents/skills/stock-analysis/
├── SKILL.md
├── skill.yaml
├── references/
│   └── execution-modes.md
└── agents/
    └── openai.yaml
~~~

SKILL.md は現在の主要Agent製品が採用しているOpen Agent Skills系の形式に合わせます。

PortableなYAML frontmatter:

~~~yaml
---
name: stock-analysis
description: Skillが何を行い、どのような依頼で利用するかを具体的に記述する。
---
~~~

互換性ルール:

- nameは小文字英数字とハイフンのみ
- nameは64文字以内
- descriptionは空でなく1024文字以内
- descriptionには「何をするか」と「いつ使うか」の両方を書く
- ベンダー固有設定をPortable frontmatterへ混ぜない
- 詳細はreferencesやscriptsへ分離しProgressive Disclosureを使う
- SKILL.md本体は簡潔に保つ

## 実行契約

標準は **host-agentモード** です。

Agent製品内でSkillを使うだけなら、別のLLM endpoint、model名、LLM API keyをユーザーへ要求しません。

親Agentが推論、財務情報の意味解釈、最終統合、自身のモデル選択、Web / Browser / MCP / File / Shell等を担当します。

決定論的Pythonは財務計算、出典公開日時チェック、Point-in-Time強制、データ正規化、決定論的抽出を担当します。

明示的にモデル切替が必要な場合だけStandalone RuntimeとProvider Adapterを使います。

## skill.yaml

skill.yaml はこのプロジェクト独自の内部メタデータです。Open Agent Skillsの必須ファイルではありません。Runtime capability、version、実行モード等を記録します。

## Agent固有sidecar

Agent固有設定はSKILL.mdから分離します。たとえば agents/openai.yaml はCodex向け表示情報を持てますが、PortableなSkill手順は変更しません。

## Tool契約

Toolの入出力はJSON serializableを基本にします。Evidenceを伴う結果は可能な限り次を持ちます。

- 安定したsource ID
- URL
- 公開 / 提出日時
- 対象期間
- 取得日時

これらをPoint-in-Time評価とprovenance検証に利用します。
