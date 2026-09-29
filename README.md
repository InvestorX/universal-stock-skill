# universal-stock-skill

**English** | [日本語](README.ja.md)

A portable Agent Skill and Python runtime for point-in-time, evidence-grounded stock analysis, with an RRSI-inspired improvement loop.

> Status: runtime foundation, EDINET API/CSV ingestion, canonical financial mapping, five-year canonical series/trends, annual-filing resolution, provider-neutral market snapshots, a J-Quants V2 market adapter with point-in-time selection, deterministic average-equity/CapEx/NOPAT derivation, automatic FinancialSnapshot assembly, and portable Agent Skill packaging are implemented.

## Overview

The project has two execution modes.

~~~mermaid
flowchart TD
    U[User request] --> S[stock-analysis Skill]
    S --> H[Current host agent]
    S --> P[Deterministic Python]
    P --> D[Financials / prices / filings / news]
    D --> P
    P --> H
    H --> R[Evidence-grounded report]

    S -. optional standalone mode .-> RT[Universal Skill Runtime]
    RT --> A[LLM Provider Adapter]
    A --> M[Explicitly configured model]
~~~

For normal Agent Skill use, the **current host agent is the reasoning engine**. Codex uses Codex, Claude Code uses Claude, Antigravity uses its active agent, and Hermes uses Hermes. The skill does not require a second LLM endpoint, model name, or API key.

The standalone Python runtime remains available for cross-model benchmarks, batch execution, application embedding, and RRSI experiments.

## Design principles

- **Host-agent first**: delegate reasoning to the current agent.
- **LLM-agnostic**: keep vendor APIs out of portable skill instructions.
- **Python for deterministic work**: calculations, source-time checks, parsing, and validation are machine-enforced.
- **Point-in-time by default**: reject information published after the analysis cutoff.
- **Evidence first**: material factual claims should remain traceable.
- **Reviewable evolution**: isolate, benchmark, and review RRSI candidates before promotion.

## Portable Agent Skill

The canonical skill bundle is:

~~~text
.agents/skills/stock-analysis/
├── SKILL.md
├── skill.yaml
├── references/
│   └── execution-modes.md
└── agents/
    └── openai.yaml
~~~

The SKILL.md manifest follows the open Agent Skills shape with portable name and description frontmatter.

Installation for Codex, Claude Code, Antigravity CLI, and Hermes Agent is documented in [docs/installation.md](docs/installation.md).

## Documentation

See [docs/README.md](docs/README.md). Every project document has a Japanese counterpart.

## Development

Python 3.11+:

~~~bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
pytest
~~~

Validate the portable skill:

~~~bash
python scripts/validate_skill.py
~~~

Install it for an agent:

~~~bash
python scripts/install_agent_skill.py --agent all --scope user
~~~

Run the synthetic metrics demo:

~~~bash
python scripts/run_analysis.py 7203 --demo
~~~
