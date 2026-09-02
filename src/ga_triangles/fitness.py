"""Fitness / error function.

Owner: whoever picks up "representation & fitness".

This is one of the questions the TP explicitly asks you to answer before
experimenting -- write the justification in docs/report, don't just pick
a metric silently.
"""

from __future__ import annotations

import numpy as np

from ga_triangles.individual import Individual


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


def fitness(individual: Individual, target: np.ndarray) -> float:
    """Fitness of `individual` against `target`. Higher = better.

    # TODO: render the individual (see render.render) and turn its error
    # against `target` into a fitness score, e.g. fitness = 1 / (1 + error)
    # or fitness = max_error - error. Cache the result on individual.fitness.
    """
    raise NotImplementedError
