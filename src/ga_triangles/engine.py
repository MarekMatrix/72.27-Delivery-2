"""Main GA loop: orchestrates selection, crossover, mutation and survival.

Owner: whoever picks up "engine & survival" -- this module is the glue
between everyone else's pieces, so it's easiest to finish last.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ga_triangles.config import GAConfig
from ga_triangles.individual import Individual
from ga_triangles.metrics import History


@dataclass
class GAResult:
    best_individual: Individual
    history: History
    n_generations_run: int
    stop_reason: str


def should_stop(generation: int, config: GAConfig, history: History) -> str | None:
    """Return a human-readable stop reason if the run should end now, else None.

    # TODO: check generation >= config.n_generations, and, if
    # config.min_error is set, whether history.best_error[-1] <= min_error.
    # Feel free to add other criteria (e.g. fitness plateau) -- document
    # them in docs/report.
    """
    raise NotImplementedError


def run_ga(target: np.ndarray, config: GAConfig) -> GAResult:
    """Run the full genetic algorithm and return the best individual found.

    # TODO:
    # 1. initialize a population of config.population_size random
    #    Individuals (see Individual.random)
    # 2. evaluate fitness of every individual against `target`
    # 3. loop until should_stop(...) returns a reason:
    #    a. select parents (selection.py, per config.selection_method)
    #    b. produce offspring via crossover (crossover.py) + mutation (mutation.py)
    #    c. evaluate offspring fitness
    #    d. form the next generation via survival.py, per config.survival_strategy
    #    e. record generation stats into a History
    # 4. return GAResult with the best individual seen, the history, and why it stopped
    """
    raise NotImplementedError
