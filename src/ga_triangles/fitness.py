"""Fitness / error function."""

from __future__ import annotations

import numpy as np

from ga_triangles.individual import Individual

from ga_triangles.render import render


def pixel_error(rendered: np.ndarray, target: np.ndarray) -> float:
    """Distance between a rendered canvas and the target image.
    Mean squared error per channel on intensities scaled to [0, 1]. 0 = identical, 1 = every channel maximally wrong. Lower = closer.
    """
    assert rendered.dtype == np.uint8
    assert rendered.shape == target.shape

    rendered = rendered / 255.0
    target = target / 255.0
    diff = rendered - target
    mse = np.mean(np.square(diff))

    return float(mse)


def fitness(individual: Individual, target: np.ndarray, k: float = 1.0) -> float:
    """Fitness of `individual` against `target`. Higher = better.
    maps error → 1/(1+k·error) (always in (0, 1]).
    Caches the result on individual.fitness
    assumes callers set individual.fitness = None after any mutation/crossover.
    """
    if individual.fitness is not None:
        return individual.fitness
    height, width = target.shape[:2]
    error = pixel_error(render(individual, width, height), target)
    score = 1/(1+k*error)
    individual.fitness = score
    return individual.fitness

