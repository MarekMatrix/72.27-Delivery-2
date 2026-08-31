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

    # TODO: pick and justify a metric (e.g. mean squared error per pixel
    # per channel, mean absolute error, 1 - SSIM, ...). Lower = closer.
    """
    raise NotImplementedError


def fitness(individual: Individual, target: np.ndarray) -> float:
    """Fitness of `individual` against `target`. Higher = better.

    # TODO: render the individual (see render.render) and turn its error
    # against `target` into a fitness score, e.g. fitness = 1 / (1 + error)
    # or fitness = max_error - error. Cache the result on individual.fitness.
    """
    raise NotImplementedError
