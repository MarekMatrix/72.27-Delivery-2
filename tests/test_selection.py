"""Tests for ga_triangles.selection. Owner: selection."""

import numpy as np

from ga_triangles import selection
from ga_triangles.individual import Individual


def make_population(fitnesses: list[float]) -> list[Individual]:
    return [Individual([], fitness=value) for value in fitnesses]


def selected_fitnesses(result: list[Individual]) -> list[float]:
    return [individual.fitness for individual in result]

def test_elite_selection_picks_best_individuals():
    population = make_population([0.2, 0.9, 0.5, 0.7])

    result = selection.select_elite(population, 3)

    assert selected_fitnesses(result) == [0.9, 0.7, 0.5]

def test_each_selection_method_returns_requested_count():
    population = make_population([0.2, 0.9, 0.5, 0.7])
    rng = np.random.default_rng(42)

    results = [
        selection.select_roulette(population, 6, rng),
        selection.select_universal(population, 6, rng),
        selection.select_ranking(population, 6, rng),
        selection.select_boltzmann(population, 6, 0.4, rng),
        selection.select_tournament_deterministic(population, 6, 3, rng),
        selection.select_tournament_probabilistic(population, 6, 0.5, rng),
    ]

    assert all(len(result) == 6 for result in results)


def test_roulette_selection_biased_toward_higher_fitness():
    population = make_population([0.0, 1.0])
    result = selection.select_roulette(population, 20, np.random.default_rng(42))

    assert all(individual.fitness == 1.0 for individual in result)


def test_universal_selection_biased_toward_higher_fitness():
    population = make_population([0.0, 1.0])
    result = selection.select_universal(population, 20, np.random.default_rng(42))

    assert all(individual.fitness == 1.0 for individual in result)


def test_ranking_uses_order_not_fitness_scale():
    first = make_population([1.0, 2.0, 3.0])
    second = make_population([100.0, 200.0, 300.0])

    first_result = selection.select_ranking(first, 1000, np.random.default_rng(42))
    second_result = selection.select_ranking(second, 1000, np.random.default_rng(42))

    assert [first_result.count(individual) for individual in first] == [
        second_result.count(individual) for individual in second
    ]


def test_deterministic_tournament_selects_best_when_tournament_is_population():
    population = make_population([0.2, 0.9, 0.5])

    result = selection.select_tournament_deterministic(
        population, 10, len(population), np.random.default_rng(42)
    )

    assert all(individual.fitness == 0.9 for individual in result)


def test_probabilistic_tournament_probability_one_selects_best():
    population = make_population([0.2, 0.9])

    result = selection.select_tournament_probabilistic(
        population, 20, 1.0, np.random.default_rng(42)
    )

    assert all(individual.fitness == 0.9 for individual in result)


def test_probabilistic_tournament_probability_zero_selects_worst():
    population = make_population([0.2, 0.9])

    result = selection.select_tournament_probabilistic(
        population, 20, 0.0, np.random.default_rng(42)
    )

    assert all(individual.fitness == 0.2 for individual in result)