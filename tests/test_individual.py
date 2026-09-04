"""Tests for ga_triangles.individual. Owner: representation & fitness."""
import numpy as np

from ga_triangles import individual
from ga_triangles.individual import Individual

def test_random_individual_has_requested_triangle_count():
    # TODO: Individual.random(n, w, h) -> len(individual.triangles) == n
    ind = Individual.random(3, np.random.default_rng(0))
    assert len(ind.triangles) == 3

def test_copy_is_independent_of_original():
    ind = Individual.random(3, np.random.default_rng(0))
    ind.fitness = 0.5
    c = ind.copy()
    c.triangles.append(c.triangles[0])
    assert len(ind.triangles) == 3 and c.fitness is None

def test_random_seed_determinism():
    ind1 = Individual.random(3, np.random.default_rng(0))
    ind2 = Individual.random(3, np.random.default_rng(0)) # identical copy
    ind3 = Individual.random(3, np.random.default_rng(1)) # different copy
    assert ind1.triangles == ind2.triangles
    assert ind1.triangles != ind3.triangles
