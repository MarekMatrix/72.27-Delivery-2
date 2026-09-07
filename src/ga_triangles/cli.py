"""Command-line entry point: `ga-triangles --image ... --triangles ...`.

Argument parsing is boilerplate and implemented in full here. It calls
straight into engine.run_ga, so this file "just works" once the rest of
the package is implemented -- no need to touch it while developing the
individual modules.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

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
    parser.add_argument(
        "--image",
        default=None,
        help="Path to the target image. Defaults to the first image file found in data/.",
    )
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


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")


def default_image_path(data_dir: str | Path = "data") -> Path:
    """Return the first image file found in data_dir, sorted by name."""
    candidates = sorted(
        p for p in Path(data_dir).iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not candidates:
        raise FileNotFoundError(f"No image files found in '{data_dir}'.")
    return candidates[0]


def make_progress_printer(n_generations: int) -> Callable[[int, int, float], None]:
    """Return a callback suitable for run_ga's on_generation, printing '\r' progress."""

    def printer(generation: int, total_generations: int, best_fitness: float) -> None:
        denom = max(total_generations, 1)
        pct = min(generation / denom, 1.0) * 100
        sys.stdout.write(
            f"\rGen {generation}/{total_generations} ({pct:5.1f}%) best_fitness={best_fitness:.4f}"
        )
        sys.stdout.flush()

    return printer


def write_run_summary(path: Path, config: GAConfig, image_path: str, result_summary: dict) -> None:
    """Write a short Markdown summary of the run's settings and outcome."""
    lines = [
        f"# Run: {path.parent.name}",
        "",
        "## Settings",
        "",
        "| Parameter | Value |",
        "|---|---|",
        f"| image | `{image_path}` |",
        f"| triangles | {config.n_triangles} |",
        f"| population_size | {config.population_size} |",
        f"| generations (max) | {config.n_generations} |",
        f"| min_error | {config.min_error} |",
        f"| selection | {config.selection_method.value} |",
        f"| crossover | {config.crossover_method.value} |",
        f"| crossover_rate | {config.crossover_rate} |",
        f"| mutation | {config.mutation_method.value} |",
        f"| mutation_rate | {config.mutation_rate} |",
        f"| survival | {config.survival_strategy.value} |",
        f"| seed | {config.random_seed} |",
        "",
        "## Result",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| generations run | {result_summary['n_generations_run']} |",
        f"| stop reason | {result_summary['stop_reason']} |",
        f"| best fitness | {result_summary['best_fitness']:.6f} |",
        "",
    ]
    path.write_text("\n".join(lines))


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)

    image_path = args.image if args.image is not None else str(default_image_path())

    config = GAConfig(
        n_triangles=args.triangles,
        target_image_path=image_path,
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

    target = load_target_image(image_path)
    result = run_ga(target, config, on_generation=make_progress_printer(config.n_generations))
    print()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    save_image(render(result.best_individual, target.shape[1], target.shape[0]), str(output_dir / "approximation.png"))
    result.history.plot(str(output_dir / "fitness.png"))

    with open(output_dir / "triangles.json", "w") as f:
        json.dump({"config": config.__dict__, "stop_reason": result.stop_reason}, f, indent=2, default=str)

    write_run_summary(
        output_dir / "run_summary.md",
        config,
        image_path,
        {
            "n_generations_run": result.n_generations_run,
            "stop_reason": result.stop_reason,
            "best_fitness": result.best_individual.fitness,
        },
    )


if __name__ == "__main__":
    main()
