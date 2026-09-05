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

import numpy as np


def crossover_one_point(parent_a: Individual, parent_b: Individual, rng: np.random.Generator) -> tuple[Individual, Individual]:
    """Single random cut point; swap the tail between both parents."""
    n = len(parent_a.triangles)
    point = rng.integers(n)

    triangles1 = parent_a.triangles[:point] + parent_b.triangles[point:]
    triangles2 = parent_b.triangles[:point] + parent_a.triangles[point:]
    individual1 = Individual(triangles1)
    individual2 = Individual(triangles2)

    return individual1, individual2


def crossover_two_point(parent_a: Individual, parent_b: Individual, rng: np.random.Generator) -> tuple[Individual, Individual]:
    """Two random cut points; swap the middle segment between both parents."""
    n = len(parent_a.triangles)
    point1 = rng.integers(n)
    point2 = rng.integers(n)

    if point1 > point2:
        point1, point2 = point2, point1 # Making sure the lowest value is assigned to point 1

    triangles1 = parent_a.triangles[:point1] + parent_b.triangles[point1:point2] + parent_a.triangles[point2:]
    triangles2 = parent_b.triangles[:point1] + parent_a.triangles[point1:point2] + parent_b.triangles[point2:]
    individual1 = Individual(triangles1)
    individual2 = Individual(triangles2)

    return individual1, individual2


def crossover_uniform(parent_a: Individual, parent_b: Individual, rng: np.random.Generator, swap_probability: float = 0.5) -> tuple[Individual, Individual]:
    """Each gene independently swapped between parents with `swap_probability`."""
    n = len(parent_a.triangles)
    swap = rng.random(n)

    triangles1 = list()
    triangles2 = list()

    for i in range(n):
        if swap[i] > swap_probability:
            triangles1.append(parent_a.triangles[i])
            triangles2.append(parent_b.triangles[i])
        else:
            triangles1.append(parent_b.triangles[i])
            triangles2.append(parent_a.triangles[i])

    individual1 = Individual(triangles1)
    individual2 = Individual(triangles2)

    return individual1, individual2



    raise NotImplementedError


# def crossover_ring(parent_a: Individual, parent_b: Individual) -> tuple[Individual, Individual]:
#     """Anular/ring crossover: genomes joined into a ring, cut at two random
#     points, offspring built by walking the ring in opposite directions."""
#     # TODO: delete this, we have 3/4
#     raise NotImplementedError
