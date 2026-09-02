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
    def random(n_triangles: int, canvas_width: int, canvas_height: int) -> "Individual":
        """Create a random individual with `n_triangles` random triangles.

        # TODO: sample random vertices within the canvas bounds and a
        # random RGBA color (including alpha) for each triangle.
        """
        raise NotImplementedError

    def copy(self) -> "Individual":
        """Return a deep copy (needed before mutating in place)."""
        # TODO: deep-copy triangles list; do NOT carry over cached fitness
        # if the copy is meant to be mutated afterwards.
        raise NotImplementedError
