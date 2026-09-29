# universal-stock-skill

A model-independent skill runtime for evidence-grounded stock analysis, with an RRSI-inspired evolution loop.

> Status: early architecture / runtime scaffold.

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

RRSI-style evolution sits outside the production runtime:

```text
current skill
    |
    v
analyze failures -> propose candidates -> benchmark -> critic
                                              |
                                              v
                                    accepted candidate
                                              |
                                              v
                                          Git / PR
                                              |
                                         human review
```

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
  architecture.md
  skill-spec.md
  benchmark-spec.md
  rrsi-design.md

src/universal_stock_skill/
  llm/                 # vendor-neutral model contract
  runtime/             # skill execution runtime
  skills/stock_analysis/
  evolution/           # evaluation / fitness / future RRSI loop

scripts/
tests/
```

## Current milestone

Version `0.1.x` focuses on the foundation:

1. vendor-neutral LLM interface
2. stock-analysis skill contract
3. deterministic tool contract
4. point-in-time benchmark format
5. multi-model evaluation
6. RRSI-inspired candidate workflow

Real financial-data connectors and provider adapters come after these contracts are stable.

## Development

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
pytest
```

See [docs/architecture.md](docs/architecture.md) for the current design.
