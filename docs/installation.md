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
| Hermes Agent | .agents/skills/stock-analysis | ~/.hermes/skills/stock-analysis | /stock-analysis |

## In this repository

Codex and Antigravity CLI can discover the checked-in .agents/skills/stock-analysis project skill directly.

Hermes also discovers project-local .agents/skills, but a repository must be trusted before those skills are loaded:

~~~bash
hermes skills trust
~~~

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

Codex uses Agent Skills compatible SKILL.md bundles. This repository keeps the portable project skill under .agents/skills/stock-analysis.

Invoke it explicitly as $stock-analysis, or let its description trigger it when relevant.

The skill does not configure an OpenAI API endpoint; it delegates to the model/auth configuration of the current Codex session.

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

Hermes detects project-local .agents/skills inside trusted Git repositories.

~~~bash
hermes skills trust
~~~

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
