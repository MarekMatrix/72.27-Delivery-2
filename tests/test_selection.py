"""Tests for ga_triangles.selection. Owner: selection."""

from ga_triangles import selection
from ga_triangles.individual import Individual
from ga_triangles.fitness import fitness
import numpy as np
import random 

random_seed = rng = np.random.default_rng(42)
population = []
for i in range(10):
    Individual_i = Individual.random(5, random_seed)
    Individual_i.fitness = 1-0.1*i
    population.append(Individual_i)
random.shuffle(population)


def test_elite_selection_picks_best_individuals():
    result = selection.select_elite(population, 6)
    #print("\n*****************************\n")
    #print("Elite selection result:")
    #print(result, type(result))
    #print("\n*****************************\n")

def test_each_selection_method_returns_requested_count():
    result = selection.select_ranking(population, 6)
    print("\n*****************************\n")
    print("Ranking selection result:")
    for individual in result:
        print(individual.fitness)
        print("\n")
    print("\n*****************************\n")

def test_roulette_selection_biased_toward_higher_fitness():
    result = selection.select_roulette(population, 6)
    print("\n*****************************\n")
    print("Roulette selection result:")
    for individual in result:
        print(individual.fitness)
        print("\n")
    print("\n*****************************\n")
    
def test_universal_selection_biased_toward_higher_fitness():
    result = selection.select_universal(population, 6)
    print("\n*****************************\n")
    print("Universal selection result:")
    for individual in result:
        print(individual.fitness)
        print("\n")
    print("\n*****************************\n")