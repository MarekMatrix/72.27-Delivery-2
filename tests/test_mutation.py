"""Tests for ga_triangles.mutation. Owner: crossover & mutation."""

import numpy as np

from ga_triangles.individual import Individual, Triangle
from ga_triangles.mutation import (
    mutate_complete,
    mutate_gene,
    mutate_multigene_limited,
    mutate_triangle,
    mutate_uniform,
)


def make_individual() -> Individual:
    return Individual.random(5, np.random.default_rng(42))


def assert_valid_individual(candidate: Individual) -> None:
    assert len(candidate.triangles) == 5
    for triangle in candidate.triangles:
        assert isinstance(triangle, Triangle)
        assert len(triangle.vertices) == 3
        assert all(len(vertex) == 2 for vertex in triangle.vertices)
        assert len(triangle.color) == 4
        assert all(0.0 <= value <= 1.0 for vertex in triangle.vertices for value in vertex)
        assert all(0.0 <= value <= 1.0 for value in triangle.color)

def test_zero_mutation_rate_leaves_individual_unchanged():
    for mutation in (mutate_gene, mutate_multigene_limited, mutate_uniform, mutate_complete):
        candidate = make_individual()
        original_triangles = candidate.triangles.copy()
        candidate.fitness = 1.0

        result = mutation(candidate, 0.0, np.random.default_rng(7))

        assert result is candidate
        assert candidate.triangles == original_triangles
        assert candidate.fitness == 1.0


def test_mutation_preserves_genome_length():
    for mutation in (mutate_gene, mutate_multigene_limited, mutate_uniform, mutate_complete):
        candidate = make_individual()

        mutation(candidate, 1.0, np.random.default_rng(7))

        assert_valid_individual(candidate)


def test_gene_mutation_invalidates_cached_fitness():
    candidate = make_individual()
    candidate.fitness = 1.0

    mutate_gene(candidate, 1.0, np.random.default_rng(7))

    assert candidate.fitness is None


def test_gene_mutation_changes_exactly_one_triangle():
    candidate = make_individual()
    original_triangles = candidate.triangles.copy()

    mutate_gene(candidate, 1.0, np.random.default_rng(7))

    changed_triangles = [
        current != original
        for current, original in zip(candidate.triangles, original_triangles)
    ]
    assert sum(changed_triangles) == 1


def test_mutated_triangle_has_valid_shape_and_values():
    candidate = make_individual()

    mutated = mutate_triangle(candidate.triangles[0], np.random.default_rng(7))

    assert_valid_individual(Individual([mutated] + candidate.triangles[1:]))


def test_uniform_and_complete_mutation_invalidate_cached_fitness():
    for mutation in (mutate_uniform, mutate_complete):
        candidate = make_individual()
        candidate.fitness = 1.0

        mutation(candidate, 1.0, np.random.default_rng(7))

        assert candidate.fitness is None
