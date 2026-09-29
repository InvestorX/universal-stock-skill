from universal_stock_skill.evolution import calculate_fitness


def test_single_model_has_no_robustness_penalty() -> None:
    result = calculate_fitness([80.0])
    assert result.fitness == 80.0
    assert result.score_stddev == 0.0


def test_cross_model_variance_reduces_fitness() -> None:
    stable = calculate_fitness([80.0, 80.0, 80.0])
    unstable = calculate_fitness([70.0, 80.0, 90.0])

    assert stable.fitness > unstable.fitness
