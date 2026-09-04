from ga_triangles.individual import Individual
from ga_triangles.survival import survival_additive, survival_exclusive


def make_individual(fitness: float) -> Individual:
    individual = Individual(triangles=[])
    individual.fitness = fitness
    return individual


def test_additive_survival_never_loses_the_best_individual():
    parents = [
        make_individual(0.95),
        make_individual(0.70),
        make_individual(0.60),
    ]

    offspring = [
        make_individual(0.90),
        make_individual(0.80),
        make_individual(0.50),
    ]

    survivors = survival_additive(parents, offspring, population_size=3)

    assert len(survivors) == 3
    assert survivors[0].fitness == 0.95
    assert [individual.fitness for individual in survivors] == [0.95, 0.90, 0.80]


def test_exclusive_survival_ignores_parents():
    parents = [
        make_individual(0.99),
    ]

    offspring = [
        make_individual(0.80),
        make_individual(0.70),
        make_individual(0.60),
    ]

    survivors = survival_exclusive(parents, offspring, population_size=3)

    assert len(survivors) == 3
    assert all(individual not in parents for individual in survivors)
    assert [individual.fitness for individual in survivors] == [0.80, 0.70, 0.60]


def test_survivor_count_matches_population_size():
    parents = [
        make_individual(0.95),
        make_individual(0.85),
        make_individual(0.75),
    ]

    offspring = [
        make_individual(0.90),
        make_individual(0.80),
        make_individual(0.70),
    ]

    additive_survivors = survival_additive(
        parents,
        offspring,
        population_size=2,
    )

    exclusive_survivors = survival_exclusive(
        parents,
        offspring,
        population_size=2,
    )

    assert len(additive_survivors) == 2
    assert len(exclusive_survivors) == 2