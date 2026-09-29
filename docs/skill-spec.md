# Skill specification

[日本語](skill-spec.ja.md)

## Portable format

The canonical distributable skill is stored at:

~~~text
.agents/skills/stock-analysis/
├── SKILL.md
├── skill.yaml
├── references/
│   └── execution-modes.md
└── agents/
    └── openai.yaml
~~~

SKILL.md follows the open Agent Skills shape used by current agent products.

Required portable YAML frontmatter:

~~~yaml
---
name: stock-analysis
description: A concrete description of what the skill does and when it should be used.
---
~~~

Portability rules:

- name uses lowercase letters, digits, and hyphens
- name is at most 64 characters
- description is non-empty and at most 1024 characters
- description states both capability and activation context
- vendor-specific behavior does not go into required frontmatter
- supporting details use progressive disclosure through references or scripts
- the core SKILL.md should remain concise

## Execution contract

The default execution mode is **host-agent**.

The skill must not ask the user for an LLM endpoint, model name, or LLM API key merely to run inside an agent product.

The host agent owns reasoning, interpretation, final synthesis, native model selection, and its native web/browser/MCP/file/shell tools.

Deterministic Python owns financial calculations, source timestamp checks, point-in-time enforcement, normalization, and deterministic extraction.

The optional standalone runtime may use Provider Adapters when the caller explicitly wants controlled model routing.

## Internal skill.yaml

skill.yaml is project metadata, not a required part of the open Agent Skills format. It records runtime capabilities, versioning, and execution policy for this repository.

## Agent-specific sidecars

Agent-specific metadata is optional and isolated from portable SKILL.md. For example, agents/openai.yaml can provide Codex-specific display metadata without changing portable instructions.

## Tool contract

Tools should use JSON-serializable inputs and outputs. Evidence-bearing results should include, when available:

- stable source identifier
- source URL
- publication or filing timestamp
- effective period
- retrieval timestamp

These fields support point-in-time evaluation and provenance checks.
