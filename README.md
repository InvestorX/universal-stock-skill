# universal-stock-skill

**English** | [日本語](README.ja.md)

A model-independent skill runtime for evidence-grounded stock analysis, with an RRSI-inspired evolution loop.

> Status: early architecture / runtime implementation.

## What this project is

The goal is to make stock-analysis knowledge portable across LLMs.

```text
Stock Analysis Skill
        |
        v
Universal Skill Runtime
        |
   +----+-----+---------+---------+
   |          |         |         |
 OpenAI    Claude    Gemini    Local LLM
   |          |         |         |
   +----------+---------+---------+
              |
              v
     deterministic Python tools
              |
              v
 financials / prices / filings / news
```

LLMs handle interpretation, hypothesis generation and reporting. Calculations, time constraints and deterministic transformations stay in Python.

## Design principles

- **LLM-agnostic**: skill definitions do not contain provider-specific instructions.
- **Python for deterministic work**: calculations, dates and data transforms are not delegated to the LLM.
- **Point-in-time by default**: benchmark cases have an `as_of` timestamp to prevent future-information leakage.
- **Evidence first**: material factual claims must be traceable to source metadata.
- **Cross-model evaluation**: a skill should work well across model families, not only the model that evolved it.
- **Reviewable evolution**: RRSI candidates are evaluated in isolation and promoted through Git/PR, never self-modified in production.

## Repository layout

```text
docs/
src/universal_stock_skill/
  llm/
  runtime/
  finance/
  benchmark/
  skills/stock_analysis/
  evolution/
scripts/
tests/
```

## Development

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
pytest
```

See [README.ja.md](README.ja.md) for the Japanese guide and [docs/architecture.md](docs/architecture.md) for the architecture.
