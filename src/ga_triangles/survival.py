"""Survival strategies for forming the next generation (both required by the TP).

Owner: whoever picks up "engine & survival".
"""

from __future__ import annotations

from ga_triangles.individual import Individual


def survival_additive(parents: list[Individual], offspring: list[Individual], population_size: int) -> list[Individual]:
    """(mu + lambda): parents and offspring compete together; keep the best
    `population_size` overall."""
    # TODO
    raise NotImplementedError


def survival_exclusive(parents: list[Individual], offspring: list[Individual], population_size: int) -> list[Individual]:
    """(mu, lambda): only offspring are eligible to survive; requires
    len(offspring) >= population_size. Keep the best `population_size` of them."""
    # TODO
    raise NotImplementedError
