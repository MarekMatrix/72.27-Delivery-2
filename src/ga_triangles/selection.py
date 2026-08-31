"""Parent/survivor selection methods, as seen in class.

Owner: whoever picks up "selection".

All functions share the same shape: given a population (already fitness-
evaluated) and how many individuals to pick, return that many individuals
(with replacement, as usual for parent selection).

Keep every method's signature identical so engine.py can swap between them
via config.SelectionMethod without special-casing.
"""

from __future__ import annotations

from ga_triangles.individual import Individual


def select_elite(population: list[Individual], n: int) -> list[Individual]:
    """Deterministically pick the `n` best individuals (with repetition if n > len)."""
    # TODO
    raise NotImplementedError


def select_roulette(population: list[Individual], n: int) -> list[Individual]:
    """Fitness-proportionate selection (a.k.a. roulette wheel)."""
    # TODO
    raise NotImplementedError


def select_universal(population: list[Individual], n: int) -> list[Individual]:
    """Stochastic universal sampling: single random offset, evenly spaced picks."""
    # TODO
    raise NotImplementedError


def select_boltzmann(population: list[Individual], n: int, temperature: float) -> list[Individual]:
    """Boltzmann selection: fitness-proportionate over a temperature-scaled
    softmax, so selection pressure changes with `temperature`."""
    # TODO
    raise NotImplementedError


def select_tournament_deterministic(population: list[Individual], n: int, tournament_size: int) -> list[Individual]:
    """Deterministic tournament: best of `tournament_size` random individuals wins, always."""
    # TODO
    raise NotImplementedError


def select_tournament_probabilistic(population: list[Individual], n: int, tournament_size: int, p: float) -> list[Individual]:
    """Probabilistic tournament: best of `tournament_size` wins with probability `p`,
    otherwise a random loser is chosen instead."""
    # TODO
    raise NotImplementedError


def select_ranking(population: list[Individual], n: int) -> list[Individual]:
    """Ranking selection: probability of selection depends on rank, not raw fitness
    (smooths out fitness-scale issues that hurt roulette)."""
    # TODO
    raise NotImplementedError
