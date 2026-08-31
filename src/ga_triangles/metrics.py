"""Per-generation metric tracking and plotting.

Owner: whoever picks up "engine & survival" (tracking); plotting helpers
are boilerplate under CLAUDE.md and implemented here in full -- extend
them as needed, no need to ask.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import matplotlib.pyplot as plt


@dataclass
class History:
    """Time series of population stats, one entry appended per generation."""

    best_fitness: list[float] = field(default_factory=list)
    mean_fitness: list[float] = field(default_factory=list)
    best_error: list[float] = field(default_factory=list)

    def record(self, best_fitness: float, mean_fitness: float, best_error: float) -> None:
        self.best_fitness.append(best_fitness)
        self.mean_fitness.append(mean_fitness)
        self.best_error.append(best_error)

    def plot(self, path: str) -> None:
        """Save a fitness-over-generations plot to `path`."""
        generations = range(1, len(self.best_fitness) + 1)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(generations, self.best_fitness, label="Best fitness")
        ax.plot(generations, self.mean_fitness, label="Mean fitness")
        ax.set_xlabel("Generation")
        ax.set_ylabel("Fitness")
        ax.set_title("Fitness evolution")
        ax.legend()
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
