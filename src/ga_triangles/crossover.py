"""Crossover operators.

Each triangle is treated as one "gene" for
these operators (crossing over whole triangles, not their sub-fields).
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

