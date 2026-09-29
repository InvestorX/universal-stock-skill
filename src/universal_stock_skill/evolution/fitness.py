from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev


@dataclass(frozen=True)
class FitnessResult:
    fitness: float
    mean_score: float
    score_stddev: float
    cost_penalty: float


def calculate_fitness(
    scores: list[float],
    *,
    robustness_penalty: float = 0.20,
    cost_penalty: float = 0.0,
) -> FitnessResult:
    if not scores:
        raise ValueError("scores must contain at least one model score")

    mean_score = fmean(scores)
    score_stddev = pstdev(scores) if len(scores) > 1 else 0.0
    fitness = mean_score - robustness_penalty * score_stddev - cost_penalty

    return FitnessResult(
        fitness=fitness,
        mean_score=mean_score,
        score_stddev=score_stddev,
        cost_penalty=cost_penalty,
    )
