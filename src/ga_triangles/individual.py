"""Genome / individual representation.

Owner: whoever picks up "representation & fitness".

Decide here:
- What exactly is a gene? (one triangle's vertices+color? one coordinate?)
- Is the genome a flat array (easier for generic crossover/mutation) or a
  list of Triangle objects (easier to read, harder to slice generically)?
This decision ripples into selection.py, crossover.py and mutation.py, so
pin it down early and document it for the rest of the group.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tests.test_individual import test_random_individual_has_requested_triangle_count


@dataclass(frozen=True)
class Triangle:
    """each gene => a translucent triangle.
    vertices: 3 (x, y) pairs, each coordinate normalised to [0, 1] to fit any canvas
              (0,0) = top-left of canvas, (1,1) = bottom-right.
    color:    (r, g, b, a), each channel normalised to a float between [0, 1].
    """
    vertices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    color: tuple[float, float, float, float]


@dataclass
class Individual:
    """A candidate image approximation: a fixed-length list of triangles."""

    triangles: list[Triangle]
    fitness: float | None = None  # cached fitness, invalidated on mutation/crossover

    @staticmethod
    def random(n_triangles: int, rng: np.random.Generator) -> "Individual":
        """Create a random individual with `n_triangles` random triangles.
        """

        def random_point() -> tuple[float, float]:
            x, y = rng.random(2)
            return float(x), float(y)

        def random_color() -> tuple[float, float, float, float]:
            r, g, b, a = rng.random(4)
            return float(r), float(g), float(b), float(a)

        triangles = []
        for _ in range(n_triangles):
            point1 = random_point()
            point2 = random_point()
            point3 = random_point()
            color = random_color()
            vertices = (point1, point2, point3)
            triangle = Triangle(vertices, color)
            triangles.append(triangle)

        return Individual(triangles)

    def copy(self) -> "Individual":
        """Return an independent copy, safe to mutate without affecting `self`.

        """
        new = self.triangles.copy()

        return Individual(new)
