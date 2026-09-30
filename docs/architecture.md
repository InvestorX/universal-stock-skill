# Architecture

[日本語](architecture.ja.md)

## Purpose

universal-stock-skill separates the stock-analysis procedure from the LLM vendor. It has two execution planes.

~~~mermaid
flowchart LR
    subgraph AgentSkill["Agent Skill plane - default"]
        U[User] --> S[stock-analysis SKILL.md]
        S --> H[Host Agent reasoning]
        S --> P[Deterministic Python]
        P --> E[Evidence and market data]
        E --> P
        P --> H
        H --> O[Structured analysis]
    end

    subgraph Standalone["Standalone runtime - optional"]
        C[CLI / Benchmark / RRSI] --> RT[SkillRuntime]
        RT --> PA[Provider Adapter]
        PA --> LM[Configured LLM]
        RT --> P2[Deterministic Python]
    end
~~~

## Agent Skill plane

This is the normal mode for Codex, Claude Code, Antigravity CLI, and Hermes Agent. The host agent already owns model selection, authentication, reasoning, and native tools, so the skill must not require a second LLM endpoint merely to execute.

The host agent performs interpretation and synthesis. Python performs deterministic calculations, parsing, and point-in-time checks. The host agent may use its available browser, web, MCP, files, or shell tools.

## Standalone runtime plane

Use the Python runtime when model routing must be controlled programmatically, such as cross-model benchmarks, RRSI evaluation, batch processing, provider experiments, or application embedding. Only this mode needs Provider Adapters or explicit endpoint configuration.

## Layering

1. Portable Skill — Agent Skills compatible SKILL.md and references.
2. Deterministic domain layer — finance, evidence, point-in-time guards, EDINET facts.
3. Host Agent execution — default reasoning path.
4. Standalone Runtime — optional programmatic orchestration.
5. Provider Adapters — optional API translation in standalone mode.
6. Evolution — RRSI-inspired candidate generation, evaluation, and promotion.

## RRSI flow

~~~mermaid
flowchart TD
    P[Production skill] --> A[Analyze failures]
    A --> C[Generate candidate]
    C --> B[Point-in-time benchmark]
    B --> X[Cross-model evaluation]
    X --> K[Critic and leakage checks]
    K -->|reject| C
    K -->|accept| PR[Branch / PR]
    PR --> HR[Human review]
    HR -->|promote| P
~~~

Production skills are never self-modified in place.
