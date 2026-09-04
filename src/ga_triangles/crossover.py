"""Crossover operators. Implement at least 2 of the 4 (TP requirement).

Owner: whoever picks up "crossover & mutation".

Depends on how individual.py represents a genome: if it's a flat array,
one/two-point and uniform crossover are direct index slicing/masking. If
it's a list of Triangle objects, treat each triangle as one "gene" for
these operators (crossing over whole triangles, not their sub-fields) --
document whichever choice you make.
"""

from __future__ import annotations

from ga_triangles.individual import Individual


def crossover_one_point(parent_a: Individual, parent_b: Individual, rng: np.random.Generator) -> tuple[Individual, Individual]:
    """Single random cut point; swap the tail between both parents."""
    gut point
    raise NotImplementedError


def crossover_two_point(parent_a: Individual, parent_b: Individual) -> tuple[Individual, Individual]:
    """Two random cut points; swap the middle segment between both parents."""
    # TODO
    raise NotImplementedError


def crossover_uniform(parent_a: Individual, parent_b: Individual, swap_probability: float = 0.5) -> tuple[Individual, Individual]:
    """Each gene independently swapped between parents with `swap_probability`."""
    # TODO
    raise NotImplementedError


def crossover_ring(parent_a: Individual, parent_b: Individual) -> tuple[Individual, Individual]:
    """Anular/ring crossover: genomes joined into a ring, cut at two random
    points, offspring built by walking the ring in opposite directions."""
    # TODO
    raise NotImplementedError
