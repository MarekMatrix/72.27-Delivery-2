"""Regression checks for parent/offspring aliasing when crossover is skipped."""

import numpy as np
import pytest

from ga_triangles import engine
from ga_triangles.config import GAConfig, SurvivalStrategy


@pytest.mark.parametrize("survival", list(SurvivalStrategy))
@pytest.mark.parametrize("repeat_parent", [False, True])
def test_skipped_crossover_preserves_parents(monkeypatch, survival, repeat_parent):
    original_select = engine.select_parents
    original_survival = engine.apply_survival
    snapshots = []
    checked = []

    def select(population, n_parents, config, rng):
        # Selection with replacement can return the same parent more than once.
        parents = ([population[0]] * n_parents if repeat_parent else
                   original_select(population, n_parents, config, rng))
        snapshots.extend((tuple(parent.triangles), parent.fitness) for parent in parents)
        return parents

    def survive(parents, offspring, config):
        # Observe the actual engine pipeline after mutation and fitness evaluation.
        assert [(tuple(parent.triangles), parent.fitness) for parent in parents] == snapshots
        assert len({id(child) for child in offspring}) == len(offspring)
        assert len({id(child.triangles) for child in offspring}) == len(offspring)
        for child in offspring:
            assert all(child is not parent for parent in parents)
            assert all(child.triangles is not parent.triangles for parent in parents)
        assert any(tuple(child.triangles) != before[0]
                   for child, before in zip(offspring, snapshots))
        checked.append(True)
        return original_survival(parents, offspring, config)

    monkeypatch.setattr(engine, "select_parents", select)
    monkeypatch.setattr(engine, "apply_survival", survive)
    config = GAConfig(n_triangles=2, population_size=2, n_generations=1,
                      crossover_rate=0.0, mutation_rate=1.0, random_seed=0,
                      survival_strategy=survival)
    engine.run_ga(np.full((8, 8, 3), 255, dtype=np.uint8), config)
    assert checked == [True]


def test_additive_survival_retains_best_when_offspring_mutate():
    # This seed previously regressed from MSE 0.0029805 to 0.0054760.
    config = GAConfig(n_triangles=2, population_size=2, n_generations=1,
                      crossover_rate=0.0, mutation_rate=1.0, random_seed=0,
                      survival_strategy=SurvivalStrategy.ADDITIVE)
    result = engine.run_ga(np.full((8, 8, 3), 255, dtype=np.uint8), config)
    assert result.history.best_error[1] <= result.history.best_error[0] + 1e-12
