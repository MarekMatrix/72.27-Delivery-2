"""Survival strategies for forming the next generation."""

from __future__ import annotations

from ga_triangles.individual import Individual


def survival_additive(
    parents: list[Individual],
    offspring: list[Individual],
    population_size: int
) -> list[Individual]:
    """(mu + lambda): parents and offspring compete together; keep the best
    `population_size` overall."""
    population = parents + offspring
    population = sorted(
        population,
        key=lambda individual: individual.fitness,
        reverse=True,
    )
    return population[:population_size]


def survival_exclusive(
    parents: list[Individual],
    offspring: list[Individual],
    population_size: int
) -> list[Individual]:
    """(mu, lambda): only offspring are eligible to survive; requires
    len(offspring) >= population_size. Keep the best `population_size` of them."""
    assert len(offspring) >= population_size

    offspring = sorted(
        offspring,
        key=lambda individual: individual.fitness,
        reverse=True,
    )
    return offspring[:population_size]