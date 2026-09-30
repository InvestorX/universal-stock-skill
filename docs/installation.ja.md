# stock-analysis Agent Skill 導入手順

[English](installation.md) | **日本語**

Skillの正本は .agents/skills/stock-analysis にあります。

通常のAgent Skill利用では、**LLM endpointの追加設定は不要**です。現在の親Agentが、自分自身のモデル・認証・Toolを使ってSkillを実行します。

## 対応表

| Host | Project配置 | User / Global配置 | 明示呼出 |
|---|---|---|---|
| Codex | .agents/skills/stock-analysis | ~/.agents/skills/stock-analysis | $stock-analysis |
| Claude Code | .claude/skills/stock-analysis | ~/.claude/skills/stock-analysis | /stock-analysis |
| Antigravity CLI | .agents/skills/stock-analysis | ~/.gemini/antigravity-cli/skills/stock-analysis | /stock-analysis |
| Hermes Agent | .agents/skills/stock-analysis | ~/.hermes/skills/stock-analysis | /stock-analysis |

## このRepository内で使う

CodexとAntigravity CLIは、commit済みの .agents/skills/stock-analysis をProject Skillとして直接検出できます。

Hermesも .agents/skills を検出しますが、初回はRepositoryをtrustします。

~~~bash
hermes skills trust
~~~

Claude CodeだけProject pathが異なるため、次を実行します。

~~~bash
python scripts/install_agent_skill.py --agent claude --scope project
~~~

## User / Global導入

~~~bash
python scripts/install_agent_skill.py --agent codex --scope user
python scripts/install_agent_skill.py --agent claude --scope user
python scripts/install_agent_skill.py --agent antigravity --scope user
python scripts/install_agent_skill.py --agent hermes --scope user
~~~

全部へ入れる場合:

~~~bash
python scripts/install_agent_skill.py --agent all --scope user
~~~

既存導入を更新する場合は --force を付けます。

## Codex

このRepositoryではPortableなProject Skillを .agents/skills/stock-analysis に配置します。

明示利用は $stock-analysis です。SkillがOpenAI API endpointを別途要求することはなく、現在のCodex sessionのmodel/auth設定へ委譲します。

公式: https://developers.openai.com/codex/skills

## Claude Code

Claude CodeはProject Skillを .claude/skills、Personal Skillを ~/.claude/skills から検出します。

~~~bash
python scripts/install_agent_skill.py --agent claude --scope project
~~~

明示利用は /stock-analysis です。SkillはClaude Code側のmodel選択、認証、Bedrock / Vertex / Gateway設定を上書きしません。

公式: https://code.claude.com/docs/en/skills

## Antigravity CLI

Project Skillは .agents/skills、Global Skillは ~/.gemini/antigravity-cli/skills に配置します。このRepositoryではProject配置済みです。

明示利用は /stock-analysis です。

公式: https://antigravity.google/docs/skills

## Hermes Agent

Hermesはtrust済みGit Repository内の .agents/skills をProject-local Skillとして検出します。

~~~bash
hermes skills trust
~~~

User導入:

~~~bash
python scripts/install_agent_skill.py --agent hermes --scope user
~~~

Codexと同じGlobal Skillを共有したい場合は ~/.hermes/config.yaml に次を追加できます。

~~~yaml
skills:
  external_dirs:
    - ~/.agents/skills
~~~

これで ~/.agents/skills/stock-analysis をCodexとHermesで共用できます。

明示利用は /stock-analysis です。

公式: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/

## Endpointを親Agentへ委譲する考え方

~~~mermaid
flowchart LR
    S[stock-analysis Skill] --> H[現在の親Agent]
    H --> N[親AgentのModel / 認証 / Native Tool]
    P[決定論的Python] --> H
~~~

Skillとして使う限り、別のendpointを設定しません。Provider Adapterを明示設定するのは、Cross-Model Benchmark、RRSI評価、Batch等のStandalone Runtimeだけです。
