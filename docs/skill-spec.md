# Skill specification

A skill is a model-independent package describing a task.

Minimum files:

```text
skills/<skill_name>/
├─ SKILL.md
└─ skill.yaml
```

A stock-analysis skill may additionally contain:

```text
workflows/
prompts/
rules/
schemas/
```

## Design constraints

A portable skill must not assume a vendor-specific API.

Avoid instructions such as:

- "call OpenAI function X"
- "use Anthropic tool_use"
- "use Gemini schema mode"

Instead describe capabilities:

- call tool
- return structured output
- cite evidence
- request missing data

The runtime translates those capabilities into each provider's native representation or a text fallback.

## Tool contract

Tools should use JSON-serializable inputs and outputs.

Each evidence-bearing result should include, when available:

- source identifier
- source URL
- publication / filing timestamp
- effective period
- retrieval timestamp

This is required for point-in-time evaluation.
