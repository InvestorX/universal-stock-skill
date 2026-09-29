# Installing the stock-analysis Agent Skill

[日本語](installation.ja.md)

The canonical skill lives at .agents/skills/stock-analysis.

Normal Agent Skill use does **not** require an additional LLM endpoint. The active host agent performs reasoning with its own configured model.

## Compatibility table

| Host | Project location | User/global location | Explicit invocation |
|---|---|---|---|
| Codex | .agents/skills/stock-analysis | ~/.agents/skills/stock-analysis | $stock-analysis |
| Claude Code | .claude/skills/stock-analysis | ~/.claude/skills/stock-analysis | /stock-analysis |
| Antigravity CLI | .agents/skills/stock-analysis | ~/.gemini/antigravity-cli/skills/stock-analysis | /stock-analysis |
| Hermes Agent | .agents/skills/stock-analysis or .hermes/skills | ~/.hermes/skills/... | /stock-analysis |

## In this repository

Codex, Antigravity CLI, and current Hermes Agent can discover the checked-in .agents/skills/stock-analysis project skill directly.

Claude Code uses a different project path:

~~~bash
python scripts/install_agent_skill.py --agent claude --scope project
~~~

## User/global install

~~~bash
python scripts/install_agent_skill.py --agent codex --scope user
python scripts/install_agent_skill.py --agent claude --scope user
python scripts/install_agent_skill.py --agent antigravity --scope user
python scripts/install_agent_skill.py --agent hermes --scope user
~~~

Install all supported hosts:

~~~bash
python scripts/install_agent_skill.py --agent all --scope user
~~~

Use --force to replace an existing installed copy.

## Codex

Codex discovers repository and user skills under .agents/skills. Invoke explicitly with $stock-analysis, or let the description trigger it implicitly.

The skill does not configure an OpenAI API endpoint; it uses the model/auth configuration of the current Codex session.

Official reference: https://developers.openai.com/codex/skills

## Claude Code

Claude Code discovers project skills under .claude/skills and personal skills under ~/.claude/skills.

~~~bash
python scripts/install_agent_skill.py --agent claude --scope project
~~~

Invoke /stock-analysis or ask a matching stock-analysis question. The skill does not override Claude Code model selection, authentication, Bedrock/Vertex routing, or gateway configuration.

Official reference: https://code.claude.com/docs/en/skills

## Antigravity CLI

Antigravity CLI supports repository skills under .agents/skills and global skills under ~/.gemini/antigravity-cli/skills. This repository already contains the project skill.

Invoke /stock-analysis.

Official reference: https://antigravity.google/docs/skills

## Hermes Agent

Current Hermes detects project-local .agents/skills inside Git repositories, so this repository works without a duplicate project copy.

For a user install:

~~~bash
python scripts/install_agent_skill.py --agent hermes --scope user
~~~

Hermes can also share the Codex user-level directory by adding this to ~/.hermes/config.yaml:

~~~yaml
skills:
  external_dirs:
    - ~/.agents/skills
~~~

That lets Codex and Hermes share one global skill copy.

Official reference: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/

## Endpoint delegation

~~~mermaid
flowchart LR
    S[stock-analysis Skill] --> H[Current host agent]
    H --> N[Host model / auth / native tools]
    P[Deterministic Python] --> H
~~~

Do not configure a second LLM endpoint merely to use this skill. Only explicit standalone tasks such as cross-model benchmarking or RRSI evaluation should configure Provider Adapters.
