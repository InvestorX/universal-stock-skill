# RRSI-inspired evolution design

This project borrows the recursive improvement idea while keeping production changes reviewable.

## Components

- **Analyst**: inspects benchmark failures and traces.
- **Proposer**: creates small candidate changes.
- **Critic**: rejects leakage, benchmark memorization and non-general changes.
- **Evaluator**: runs point-in-time and cross-model benchmarks.
- **Fitness**: combines quality, robustness and cost.
- **Promoter**: opens a PR for accepted candidates.

## Editable surface

Early versions may edit only:

- prompts
- workflow ordering
- evidence rules
- tool-selection policy
- structured output schemas

Later versions may edit runtime code only under stricter tests.

## Safety boundaries

- Never mutate `main` or the deployed skill directly.
- Every candidate is isolated in a branch/worktree.
- Require held-out cases.
- Keep complete experiment metadata.
- Human review is required before production promotion.
