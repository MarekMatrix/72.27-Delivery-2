"""Command-line entry point: `ga-triangles --image ... --triangles ...`.

Argument parsing is boilerplate and implemented in full here. It calls
straight into engine.run_ga.
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
from ga_triangles.engine import run_ga, run_ga_chunked
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
    parser.add_argument(
        "--max-image-size",
        type=int,
        default=None,
        help="Downscale the target image so its longer side is at most this many pixels "
             "(aspect ratio preserved, never upscales). Speeds up rendering/fitness a lot.",
    )
    parser.add_argument(
        "--triangle-max-offset",
        type=float,
        default=None,
        help="If set, initial triangles are built from one random anchor point plus the "
             "other two vertices offset by at most this much (in [0,1] canvas units), "
             "biasing the initial population toward smaller triangles. Default: fully "
             "independent random vertices (can be large).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="If set, split the target image into --chunk-size x --chunk-size pieces, "
             "run an independent GA on each at full resolution, and recombine into the "
             "final image. Combine with --max-image-size to chunk a downscaled image "
             "(resize is applied first). Triangles cannot cross chunk boundaries, so "
             "expect visible seams.",
    )
    parser.add_argument(
        "--chunk-generations",
        type=int,
        default=None,
        help="Generations to run per chunk when --chunk-size is set (each chunk is a much "
             "smaller subproblem than the full image, so it can converge in far fewer "
             "generations). Defaults to --generations if not given. Ignored without "
             "--chunk-size.",
    )

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


def make_chunk_progress_printer(n_chunks: int) -> Callable[[int, int, int, int, float], None]:
    """Return a callback suitable for run_ga_chunked's on_chunk_generation.

    Prints '\r' progress within a chunk's run, and a trailing newline once
    that chunk finishes so each chunk leaves one final line behind.
    """

    def printer(
        chunk_index: int,
        n_chunks_: int,
        generation: int,
        n_generations: int,
        best_fitness: float,
    ) -> None:
        denom = max(n_generations, 1)
        pct = min(generation / denom, 1.0) * 100
        end = "\n" if generation >= n_generations else ""
        sys.stdout.write(
            f"\rChunk {chunk_index + 1}/{n_chunks_} | "
            f"Gen {generation}/{n_generations} ({pct:5.1f}%) best_fitness={best_fitness:.4f}{end}"
        )
        sys.stdout.flush()

    return printer


def write_chunked_run_summary(
    path: Path,
    config: GAConfig,
    image_path: str,
    chunk_size: int,
    chunk_generations: int,
    chunked_result,
) -> None:
    """Write a short Markdown summary of a chunked run's settings and outcome."""
    fitnesses = [result.best_individual.fitness for result, _ in chunked_result.chunk_results]

    lines = [
        f"# Chunked run: {path.parent.name}",
        "",
        "## Settings",
        "",
        "| Parameter | Value |",
        "|---|---|",
        f"| image | `{image_path}` |",
        f"| chunk_size | {chunk_size} |",
        f"| chunk_generations | {chunk_generations} |",
        f"| triangles per chunk | {config.n_triangles} |",
        f"| initial_triangle_max_offset | {config.initial_triangle_max_offset} |",
        f"| population_size | {config.population_size} |",
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
        f"| chunks | {len(chunked_result.chunk_results)} |",
        f"| mean best fitness | {sum(fitnesses) / len(fitnesses):.6f} |",
        f"| min best fitness | {min(fitnesses):.6f} |",
        f"| max best fitness | {max(fitnesses):.6f} |",
        "",
    ]
    path.write_text("\n".join(lines))


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
        f"| initial_triangle_max_offset | {config.initial_triangle_max_offset} |",
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
        initial_triangle_max_offset=args.triangle_max_offset,
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

    target = load_target_image(image_path, max_size=args.max_image_size)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.chunk_size is not None:
        chunk_generations = args.chunk_generations if args.chunk_generations is not None else args.generations
        n_chunks = len(range(0, target.shape[0], args.chunk_size)) * len(range(0, target.shape[1], args.chunk_size))

        chunked_result = run_ga_chunked(
            target,
            config,
            chunk_size=args.chunk_size,
            chunk_generations=chunk_generations,
            on_chunk_generation=make_chunk_progress_printer(n_chunks),
        )

        save_image(chunked_result.final_image, str(output_dir / "approximation.png"))

        write_chunked_run_summary(
            output_dir / "run_summary.md",
            config,
            image_path,
            args.chunk_size,
            chunk_generations,
            chunked_result,
        )
    else:
        result = run_ga(target, config, on_generation=make_progress_printer(config.n_generations))
        print()

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
