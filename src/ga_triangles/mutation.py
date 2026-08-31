"""Mutation operators. Implement at least 2 of the 4 (TP requirement).

Owner: whoever picks up "crossover & mutation".

All operators mutate in place (or return a mutated copy -- pick one
convention and use it consistently) with probability/rate `mutation_rate`.
"""

from __future__ import annotations

from ga_triangles.individual import Individual


def mutate_gene(individual: Individual, mutation_rate: float) -> Individual:
    """Pick exactly one gene and perturb it (classic single-point mutation)."""
    # TODO
    raise NotImplementedError


def mutate_multigene(individual: Individual, mutation_rate: float) -> Individual:
    """Each gene independently mutated with probability `mutation_rate`."""
    # TODO
    raise NotImplementedError


def mutate_uniform(individual: Individual, mutation_rate: float) -> Individual:
    """Replace a mutated gene's value with a fresh random value (uniform in its domain)."""
    # TODO
    raise NotImplementedError


def mutate_non_uniform(individual: Individual, mutation_rate: float, generation: int, max_generations: int) -> Individual:
    """Perturbation magnitude shrinks as `generation` approaches `max_generations`
    (fine-tunes late, explores early)."""
    # TODO
    raise NotImplementedError
