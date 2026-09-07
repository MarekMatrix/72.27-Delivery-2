"""Hyperparameter container for a GA run.

Pure data holder -- no logic lives here. Whoever owns engine.py decides
which of these are actually read; add fields as the engine needs them.
"""

from dataclasses import dataclass, field
from enum import Enum


class SelectionMethod(str, Enum):
    ELITE = "elite"
    ROULETTE = "roulette"
    UNIVERSAL = "universal"
    BOLTZMANN = "boltzmann"
    TOURNAMENT_DETERMINISTIC = "tournament_deterministic"
    TOURNAMENT_PROBABILISTIC = "tournament_probabilistic"
    RANKING = "ranking"


class CrossoverMethod(str, Enum):
    ONE_POINT = "one_point"
    TWO_POINT = "two_point"
    UNIFORM = "uniform"
    RING = "ring"


class MutationMethod(str, Enum):
    GENE = "gene"
    MULTIGENE = "multigene"
    UNIFORM = "uniform"
    NON_UNIFORM = "non_uniform"


class SurvivalStrategy(str, Enum):
    ADDITIVE = "additive"     # (mu + lambda): parents and offspring compete
    EXCLUSIVE = "exclusive"   # (mu, lambda): only offspring survive


@dataclass
class GAConfig:
    # Problem parameters (not hyperparameters, see TP statement)
    n_triangles: int = 50
    target_image_path: str = ""
    initial_triangle_max_offset: float | None = None  # None = fully random triangles

    # Population / evolution hyperparameters
    population_size: int = 100
    n_generations: int = 500
    min_error: float | None = None  # optional early-stop threshold

    selection_method: SelectionMethod = SelectionMethod.ELITE
    tournament_size: int = 3
    tournament_probability: float = 0.75  # for probabilistic tournament
    boltzmann_temperature: float = 1.0

    crossover_method: CrossoverMethod = CrossoverMethod.ONE_POINT
    crossover_rate: float = 0.9

    mutation_method: MutationMethod = MutationMethod.GENE
    mutation_rate: float = 0.05

    survival_strategy: SurvivalStrategy = SurvivalStrategy.ADDITIVE

    random_seed: int | None = None

    extra: dict = field(default_factory=dict)  # escape hatch for one-off experiment knobs
