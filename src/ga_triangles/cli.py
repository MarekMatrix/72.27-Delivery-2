"""Command-line entry point: `ga-triangles --image ... --triangles ...`.

Argument parsing is boilerplate and implemented in full here. It calls
straight into engine.run_ga.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from ga_triangles.config import (
    CrossoverMethod,
    GAConfig,
    MutationMethod,
    SelectionMethod,
    SurvivalStrategy,
)
from ga_triangles.engine import run_ga
from ga_triangles.image_io import load_target_image, save_image
from ga_triangles.render import render


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Approximate an image with GA-evolved triangles.")
    parser.add_argument("--image", required=True, help="Path to the target image.")
    parser.add_argument("--triangles", type=int, required=True, help="Number of triangles to use.")
    parser.add_argument("--output-dir", default="results", help="Where to write outputs.")

    parser.add_argument("--population-size", type=int, default=100)
    parser.add_argument("--generations", type=int, default=500)
    parser.add_argument("--min-error", type=float, default=None)

    parser.add_argument("--selection", choices=[m.value for m in SelectionMethod], default=SelectionMethod.ELITE.value)
    parser.add_argument("--crossover", choices=[m.value for m in CrossoverMethod], default=CrossoverMethod.ONE_POINT.value)
    parser.add_argument("--mutation", choices=[m.value for m in MutationMethod], default=MutationMethod.GENE.value)
    parser.add_argument("--survival", choices=[m.value for m in SurvivalStrategy], default=SurvivalStrategy.ADDITIVE.value)

    parser.add_argument("--mutation-rate", type=float, default=0.05)
    parser.add_argument("--crossover-rate", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=None)
    return parser


def config_from_args(args: argparse.Namespace) -> GAConfig:
    """Share the exact effective configuration with the experiment runner."""
    return GAConfig(
        n_triangles=args.triangles,
        target_image_path=args.image,
        population_size=args.population_size,
        n_generations=args.generations,
        min_error=args.min_error,
        selection_method=SelectionMethod(args.selection),
        crossover_method=CrossoverMethod(args.crossover),
        mutation_method=MutationMethod(args.mutation),
        survival_strategy=SurvivalStrategy(args.survival),
        mutation_rate=args.mutation_rate,
        crossover_rate=args.crossover_rate,
        random_seed=args.seed,
    )


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    config = config_from_args(args)
    target = load_target_image(args.image)
    ga_start = time.perf_counter()
    result = run_ga(target, config)
    ga_elapsed_s = time.perf_counter() - ga_start

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    save_image(render(result.best_individual, target.shape[1], target.shape[0]), str(output_dir / "approximation.png"))
    result.history.plot(str(output_dir / "fitness.png"))

    with open(output_dir / "triangles.json", "w") as f:
        json.dump({
            "config": config.__dict__,
            "canvas": {"width": target.shape[1], "height": target.shape[0],
                       "background_rgb": [255, 255, 255]},
            # Preserve drawing order; later triangles are painted on top.
            "triangles": [
                {"vertices": [[float(x), float(y)] for x, y in triangle.vertices],
                 "color": [float(channel) for channel in triangle.color]}
                for triangle in result.best_individual.triangles
            ],
            "ga_elapsed_s": ga_elapsed_s,
            "stop_reason": result.stop_reason,
            "n_generations_run": result.n_generations_run,
            "final_fitness": result.best_individual.fitness,
            "final_error": float(result.history.best_error[-1]),
            "fitness_history": result.history.best_fitness,
            "error_history": result.history.best_error,
        }, f, indent=2, default=str)


if __name__ == "__main__":
    main()
