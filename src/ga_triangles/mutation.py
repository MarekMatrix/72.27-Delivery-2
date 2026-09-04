"""Mutation operators. Implement at least 2 of the 4 (TP requirement).

Owner: whoever picks up "crossover & mutation".

All operators mutate in place (or return a mutated copy -- pick one
convention and use it consistently) with probability/rate `mutation_rate`.
"""

from __future__ import annotations

from ga_triangles.individual import Individual, Triangle
import numpy as np

def mutate_gene(individual: Individual, mutation_rate: float, rng: np.random.Generator) -> Individual:
    """Pick exactly one gene and perturb it (classic single-point mutation)."""
    r = rng.random()
    if r <= mutation_rate: 
        index = rng.integers(0, len(individual.triangles))
        individual.triangles[index] = mutate_triangle(individual.triangles[index], rng)
        individual.fitness = None
    return individual

def mutate_multigene_limited(individual: Individual, mutation_rate: float, rng: np.random.Generator) -> Individual:
    """Each selected gene independently mutated with probability `mutation_rate`."""
    M = rng.integers(0, len(individual.triangles))
    indexes = rng.choice(range(len(individual.triangles)), size=M, replace=False)
    for index in indexes: 
        r = rng.random()
        if r <= mutation_rate:
            individual.triangles[index] = mutate_triangle(individual.triangles[index], rng)
            individual.fitness = None
    return individual

def mutate_uniform(individual: Individual, mutation_rate: float, rng: np.random.Generator) -> Individual:
    """Uniform mutation: each gene (triangle) is independently selected for mutation with probability mutation_rate."""
    for index in range(len(individual.triangles)): 
        r = rng.random()
        if r <= mutation_rate:
            individual.triangles[index] = mutate_triangle(individual.triangles[index], rng)
            individual.fitness = None
    return individual

def mutate_complete(individual: Individual, mutation_rate: float, rng: np.random.Generator) -> Individual: 
    """Replace all genes with probability `mutation_rate`."""
    r = rng.random()
    if r <= mutation_rate:
        individual.fitness = None
        for index in range(len(individual.triangles)): 
            individual.triangles[index] = mutate_triangle(individual.triangles[index], rng)
    return individual

def mutate_triangle(triangle: Triangle, rng: np.random.Generator) -> Triangle:
    """Replaces one gen parameter of the triangle."""
    vertices = [list(vertex) for vertex in triangle.vertices]
    color = list(triangle.color)
    
    component_type = rng.integers(0,2)
    if component_type == 0:
        vertex_index = rng.integers(0,3)
        coordinate_index = rng.integers(0,2)
        vertices[vertex_index][coordinate_index] = rng.random()
    else: 
        color_index = rng.integers(0,4)
        color[color_index] = rng.random()
    
    triangle = Triangle(tuple(tuple(vertex) for vertex in vertices), tuple(color))
    return triangle


#def mutate_non_uniform(individual: Individual, mutation_rate: float, rng: np.random.Generator) -> Individual:
#    return

# Dont know what would be non uniform
"""
mutate_gene: choose one triangle and slightly change one coordinate, color channel, or alpha.
mutate_multigene_limited: independently perturb several triangles.
mutate_uniform: mutates selected triangles.
mutate_complete: mutates all triangles.
"""