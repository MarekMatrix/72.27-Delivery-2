"""Main GA loop: orchestrates selection, crossover, mutation and survival.

Owner: whoever picks up "engine & survival" -- this module is the glue
between everyone else's pieces, so it's easiest to finish last.
"""



from __future__ import annotations

from dataclasses import dataclass
import random

import numpy as np

from ga_triangles.fitness import fitness, pixel_error
from ga_triangles.individual import Individual
from ga_triangles.metrics import History
from ga_triangles.render import render

from ga_triangles.selection import (
    select_elite,
    select_roulette,
    select_universal,
    select_boltzmann,
    select_tournament_deterministic,
    select_tournament_probabilistic,
    select_ranking,
)

from ga_triangles.config import (
    GAConfig,
    MutationMethod,
    SelectionMethod,
    SurvivalStrategy,
)

from ga_triangles.mutation import (
    mutate_gene,
    mutate_multigene_limited,
    mutate_uniform,
)

from ga_triangles.survival import (
    survival_additive,
    survival_exclusive,
)

from ga_triangles.crossover import (
    crossover_one_point,
    crossover_two_point,
    crossover_uniform,
)
from ga_triangles.config import CrossoverMethod  

@dataclass
class GAResult:
    best_individual: Individual
    history: History
    n_generations_run: int
    stop_reason: str


def should_stop(generation: int, config: GAConfig, history: History) -> str | None:
    """Return a human-readable stop reason if the run should end now, else None."""

    if generation >= config.n_generations:
        return "maximum generations reached"

    if (
        config.min_error is not None
        and history.best_error
        and history.best_error[-1] <= config.min_error
    ):
        return "minimum error reached"

    return None

def select_parents(
    population: list[Individual],
    n_parents: int,
    config: GAConfig,
) -> list[Individual]:
    """Select parents using the selection method specified in the config."""

    if config.selection_method == SelectionMethod.ELITE:
        return select_elite(population, n_parents)

    if config.selection_method == SelectionMethod.ROULETTE:
        return select_roulette(population, n_parents)

    if config.selection_method == SelectionMethod.UNIVERSAL:
        return select_universal(population, n_parents)

    if config.selection_method == SelectionMethod.BOLTZMANN:
        return select_boltzmann(
            population,
            n_parents,
            config.boltzmann_temperature,
        )

    if config.selection_method == SelectionMethod.TOURNAMENT_DETERMINISTIC:
        return select_tournament_deterministic(
            population,
            n_parents,
            config.tournament_size,
        )

    if config.selection_method == SelectionMethod.TOURNAMENT_PROBABILISTIC:
        return select_tournament_probabilistic(
            population,
            n_parents,
            config.tournament_probability,
        )

    if config.selection_method == SelectionMethod.RANKING:
        return select_ranking(population, n_parents)

    raise ValueError(f"Unknown selection method: {config.selection_method}")


def apply_mutation(
    individual: Individual,
    config: GAConfig,
    rng: np.random.Generator,
) -> Individual:
    """Apply the mutation method specified in the config."""

    if config.mutation_method == MutationMethod.GENE:
        return mutate_gene(
            individual,
            config.mutation_rate,
            rng,
        )

    if config.mutation_method == MutationMethod.MULTIGENE:
        return mutate_multigene_limited(
            individual,
            config.mutation_rate,
            rng,
        )

    if config.mutation_method == MutationMethod.UNIFORM:
        return mutate_uniform(
            individual,
            config.mutation_rate,
            rng,
        )

    if config.mutation_method == MutationMethod.NON_UNIFORM:
        raise NotImplementedError(
            "Non-uniform mutation is not implemented."
        )

    raise ValueError(
        f"Unknown mutation method: {config.mutation_method}"
    )



def apply_survival(
    parents: list[Individual],
    offspring: list[Individual],
    config: GAConfig,
) -> list[Individual]:
    """Apply the survival strategy specified in the config."""

    if config.survival_strategy == SurvivalStrategy.ADDITIVE:
        return survival_additive(
            parents,
            offspring,
            config.population_size,
        )

    if config.survival_strategy == SurvivalStrategy.EXCLUSIVE:
        return survival_exclusive(
            parents,
            offspring,
            config.population_size,
        )

    raise ValueError(
        f"Unknown survival strategy: {config.survival_strategy}"
    )

def record_population_metrics(
    population: list[Individual],
    target: np.ndarray,
    history: History,
) -> Individual:
    """Record best fitness, mean fitness and best error for the population."""

    best_individual = max(
        population,
        key=lambda individual: individual.fitness,
    )

    mean_fitness = float(
        np.mean([individual.fitness for individual in population])
    )

    height, width = target.shape[:2]

    best_error = pixel_error(
        render(best_individual, width, height),
        target,
    )

    history.record(
        best_fitness=best_individual.fitness,
        mean_fitness=mean_fitness,
        best_error=best_error,
    )

    return best_individual


def run_ga(target: np.ndarray, config: GAConfig) -> GAResult:
    """Run the full genetic algorithm and return the best individual found."""

    rng = np.random.default_rng(config.random_seed)

    if config.random_seed is not None:
        random.seed(config.random_seed)

    population = [
        Individual.random(config.n_triangles, rng)
        for _ in range(config.population_size)
    ]

    for individual in population:
        fitness(individual, target)

    history = History()

    best_individual = record_population_metrics(
        population,
        target,
        history,
    )

    generation = 0

    while True:
        stop_reason = should_stop(generation, config, history)

        if stop_reason is not None:
            break

        # Selection
        parents = select_parents(
            population,
            config.population_size,
            config,
        )

        # Crossover
        offspring = []
        for i in range(0, len(parents) - 1, 2):
            a, b = parents[i], parents[i + 1]
            if rng.random() < config.crossover_rate:
                if config.crossover_method == CrossoverMethod.ONE_POINT:
                    child_a, child_b = crossover_one_point(a, b, rng)
                elif config.crossover_method == CrossoverMethod.TWO_POINT:
                    child_a, child_b = crossover_two_point(a, b, rng)
                elif config.crossover_method == CrossoverMethod.UNIFORM:
                    child_a, child_b = crossover_uniform(a, b, rng)
                else:
                    raise ValueError(f"Unknown crossover method: {config.crossover_method}")
            else:
                child_a, child_b = a, b
            offspring.extend([child_a, child_b])

    
        # Mutasjon
        offspring = [apply_mutation(ind, config, rng) for ind in offspring]

        # Fitness
        for ind in offspring:
            fitness(ind, target)

        # Survival
        population = apply_survival(parents, offspring, config)

        # Metrics
        best_individual = record_population_metrics(population, target, history)
        generation += 1

    return GAResult(
        best_individual=best_individual,
        history=history,
        n_generations_run=generation,
        stop_reason=stop_reason,
    )
