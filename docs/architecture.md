# Architecture

## Purpose

`universal-stock-skill` separates stock-analysis knowledge from the LLM that executes it.

The project has five layers:

1. **Skill specification** — portable analysis procedure, prompts, rules, schemas and tool contracts.
2. **Runtime** — loads a skill, validates inputs, dispatches tools and calls an LLM provider.
3. **LLM adapters** — normalize OpenAI, Anthropic, Gemini, LiteLLM, Ollama and OpenAI-compatible APIs.
4. **Stock tools** — deterministic data retrieval and calculations.
5. **Evolution** — RRSI-inspired candidate generation, evaluation and promotion.

## Core rule

Deterministic work belongs in Python. LLMs interpret the results.

Examples:

- price history, ratios, CAGR, margins, ROIC: Python
- source collection and timestamps: Python
- explanation, hypothesis generation, risk synthesis: LLM
- final prose report: LLM

This reduces arithmetic hallucinations and makes cross-model evaluation possible.

## Runtime flow

```text
request
  |
  v
SkillLoader
  |
  v
SkillRuntime ----> ToolRegistry ----> market / filings / financial data
  |
  v
LLMProvider
  |
  v
validated structured result
```

## Evolution flow

```text
production skill
      |
      v
candidate proposer
      |
      +--> candidate A
      +--> candidate B
      |
      v
point-in-time benchmark
      |
      v
cross-model evaluation
      |
      v
critic / leakage checks
      |
      v
accepted candidate -> PR -> human promotion
```

Production skills are never self-modified in place.
