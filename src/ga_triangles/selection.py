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
import math
import numpy as np
import random
from itertools import accumulate


def select_elite(population: list[Individual], K: int) -> list[Individual]:
    """Deterministically pick the `K` best individuals (with repetition if K > N)."""
    N = len(population)
    elite = sorted(population, key=lambda individual: individual.fitness, reverse=True)
    selected = []
    for i, individual in enumerate(elite):
        for _ in range(math.ceil((K-i)/N)):
            selected.append(individual)
    assert len(selected) >= K
    selected = selected[:K]
    return selected


def select_roulette(population: list[Individual], K: int, fitness=None) -> list[Individual]:
    """Fitness-proportionate selection (a.k.a. roulette wheel)."""
    if fitness == None: 
        fitness = [individual.fitness for individual in population]
    total_fitness = sum(fitness) 
    relative_fitness = [individual_fitness/total_fitness for individual_fitness in fitness]
    accumulated_fitness = list(accumulate(relative_fitness))
    r = sorted([random.random() for _ in range(K)])
    selected = []
    i, j = 0, 0
    while i < K:
        if r[i] <= accumulated_fitness[j]:
            selected.append(population[j])
            i += 1; j -= 1
        j += 1
    return selected


def select_universal(population: list[Individual], K: int) -> list[Individual]:
    """Stochastic universal sampling: single random offset, evenly spaced picks."""
    total_fitness = sum(individual.fitness for individual in population) 
    relative_fitness = [individual.fitness/total_fitness for individual in population]
    accumulated_fitness = list(accumulate(relative_fitness))
    offset = random.random()
    r = [(offset + j) / K  for j in range(K)]
    selected = []
    i, j = 0, 0
    while i < K:
        if r[i] <= accumulated_fitness[j]:
            selected.append(population[j])
            i += 1; j -= 1
        j += 1
    return selected


def select_ranking(population: list[Individual], K: int) -> list[Individual]:
    """Ranking selection: probability of selection depends on rank, not raw fitness
    (smooths out fitness-scale issues that hurt roulette)."""
    N = len(population)
    sorted_indices = sorted(range(N), key=lambda i: population[i].fitness, reverse=True)
    rank = [0]*N
    for pos, idx in enumerate(sorted_indices):
        rank[idx] = pos
    rank_fitness = [(N - rank[i]) / N for i in range(N)]
    selected = select_roulette(population, K, rank_fitness)
    return selected


def select_boltzmann(population: list[Individual], K: int, temperature: float) -> list[Individual]:
    """Boltzmann selection: fitness-proportionate over a temperature-scaled
    softmax, so selection pressure changes with `temperature`."""
    temperature = max(temperature, 1e-6)  # avoid divide-by-zero
    N = len(population)
    promedio = sum(np.exp(individual.fitness/temperature) for individual in population) / N
    boltzmann_fitness = [np.exp(individual.fitness/temperature)/promedio for individual in population]
    selected = select_roulette(population, K, boltzmann_fitness)
    return selected


def select_tournament_deterministic(population: list[Individual], K: int, tournament_size: int) -> list[Individual]:
    """Deterministic tournament: best of `tournament_size` random individuals wins, always."""
    assert tournament_size <= len(population)
    selected = []
    for _ in range(K):
        subpopulation = random.sample(population, tournament_size)
        winner = subpopulation[max((i for i in range(tournament_size)), key=lambda i: subpopulation[i].fitness)]
        selected.append(winner)
    return selected

def select_tournament_probabilistic(population: list[Individual], K: int, p: float) -> list[Individual]:
    """Probabilistic tournament: best of `tournament_size` wins with probability `p`,
    otherwise a random loser is chosen instead."""
    selected = []
    for _ in range(K):
        duel = random.sample(population, 2)
        duel = sorted(duel, key=lambda individual: individual.fitness, reverse=True)
        r = random.random()
        if r > p:
            winner = duel[0]
        else:
            winner = duel[1]
        selected.append(winner)
    return selected

