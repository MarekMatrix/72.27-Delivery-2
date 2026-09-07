import numpy as np

from ga_triangles.config import GAConfig, SurvivalStrategy
from ga_triangles.engine import should_stop, record_population_metrics, apply_survival
from ga_triangles.metrics import History
from ga_triangles.individual import Individual





def test_should_stop_at_max_generations():
    config = GAConfig(n_generations=10)
    history = History()

    reason = should_stop(10, config, history)

    assert reason == "maximum generations reached"


def test_should_stop_when_min_error_reached():
    config = GAConfig(
        n_generations=100,
        min_error=0.1,
    )
    history = History()
    history.best_error.append(0.08)

    reason = should_stop(20, config, history)

    assert reason == "minimum error reached"


def test_should_continue():
    config = GAConfig(
        n_generations=100,
        min_error=0.1,
    )
    history = History()
    history.best_error.append(0.2)

    reason = should_stop(20, config, history)

    assert reason is None


def test_record_population_metrics_adds_history_entry():
    rng = np.random.default_rng(42)

    population = [
        Individual.random(2, rng),
        Individual.random(2, rng),
    ]

    population[0].fitness = 0.8
    population[1].fitness = 0.6

    target = np.zeros((10, 10, 3), dtype=np.uint8)
    history = History()

    best = record_population_metrics(
        population,
        target,
        history,
    )

    assert best is population[0]
    assert len(history.best_fitness) == 1
    assert len(history.mean_fitness) == 1
    assert len(history.best_error) == 1

    assert history.best_fitness[0] == 0.8
    assert history.mean_fitness[0] == 0.7

def test_apply_survival_uses_additive_strategy():
    rng = np.random.default_rng(1)

    parents = [
        Individual.random(1, rng),
        Individual.random(1, rng),
    ]
    offspring = [
        Individual.random(1, rng),
        Individual.random(1, rng),
    ]

    parents[0].fitness = 0.9
    parents[1].fitness = 0.8
    offspring[0].fitness = 0.7
    offspring[1].fitness = 0.6

    config = GAConfig(
        population_size=2,
        survival_strategy=SurvivalStrategy.ADDITIVE,
    )

    survivors = apply_survival(
        parents,
        offspring,
        config,
    )

    assert survivors == [parents[0], parents[1]]

def test_apply_survival_uses_exclusive_strategy():
    rng = np.random.default_rng(2)

    parents = [
        Individual.random(1, rng),
        Individual.random(1, rng),
    ]
    offspring = [
        Individual.random(1, rng),
        Individual.random(1, rng),
    ]

    parents[0].fitness = 0.9
    parents[1].fitness = 0.8
    offspring[0].fitness = 0.7
    offspring[1].fitness = 0.6

    config = GAConfig(
        population_size=2,
        survival_strategy=SurvivalStrategy.EXCLUSIVE,
    )

    survivors = apply_survival(
        parents,
        offspring,
        config,
    )

    assert survivors == offspring