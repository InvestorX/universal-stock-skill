# RRSI-inspired evolution design

[日本語](rrsi-design.ja.md)

This project borrows the recursive improvement idea while keeping production changes reviewable.

## Components

- **Analyst**: inspects benchmark failures and traces
- **Proposer**: creates small candidate changes
- **Critic**: rejects leakage, benchmark memorization and non-general changes
- **Evaluator**: runs point-in-time and cross-model benchmarks
- **Fitness**: combines quality, robustness and cost
- **Promoter**: opens a PR for accepted candidates

## Editable surface

Early versions may edit only:

- prompts and skill instructions
- workflow ordering
- evidence rules
- tool-selection policy
- structured output schemas

Later versions may edit runtime code only under stricter tests.

## Safety boundaries

- never mutate main or the deployed skill directly
- isolate every candidate in a branch/worktree
- require held-out cases
- keep complete experiment metadata
- require human review before production promotion
