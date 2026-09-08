"""Command-line entry point: `ga-triangles --image ... --triangles ...`."""

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
from ga_triangles.engine import GAResult, run_ga, run_ga_chunked
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
        help="Downscale the target so its longer side is at most this many pixels.",
    )
    parser.add_argument(
        "--triangle-max-offset",
        type=float,
        default=None,
        help="Keep initial triangles small: the other two vertices stay within this "
             "offset (in [0,1]) of the first. Default: fully random vertices.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Split the target into chunk-size x chunk-size tiles and evolve each "
             "one separately, then stitch them back together (seams are expected).",
    )
    parser.add_argument(
        "--chunk-generations",
        type=int,
        default=None,
        help="Generations per chunk when --chunk-size is set. Defaults to --generations.",
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
    """on_generation callback that overwrites a single line with gen/pct/fitness."""

    def printer(generation: int, total_generations: int, best_fitness: float) -> None:
        denom = max(total_generations, 1)
        pct = min(generation / denom, 1.0) * 100
        sys.stdout.write(
            f"\rGen {generation}/{total_generations} ({pct:5.1f}%) best_fitness={best_fitness:.4f}"
        )
        sys.stdout.flush()

    return printer


def make_chunk_progress_printer(n_chunks: int) -> Callable[[int, int, int, int, float], None]:
    """on_chunk_generation callback: one live line per chunk, closed with a
    newline when the chunk's last generation lands."""

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


def _write_summary(
    path: Path,
    title: str,
    settings: list[tuple[str, object]],
    results: list[tuple[str, object]],
) -> None:
    """Write a run_summary.md with a settings table and a results table."""

    def table(rows: list[tuple[str, object]], key_header: str) -> str:
        header = [f"| {key_header} | Value |", "|---|---|"]
        return "\n".join(header + [f"| {key} | {value} |" for key, value in rows])

    path.write_text(
        f"# {title}\n\n"
        f"## Settings\n\n{table(settings, 'Parameter')}\n\n"
        f"## Result\n\n{table(results, 'Metric')}\n"
    )


def _common_settings(config: GAConfig, image_path: str) -> list[tuple[str, object]]:
    return [
        ("image", f"`{image_path}`"),
        ("initial_triangle_max_offset", config.initial_triangle_max_offset),
        ("population_size", config.population_size),
        ("selection", config.selection_method.value),
        ("crossover", config.crossover_method.value),
        ("crossover_rate", config.crossover_rate),
        ("mutation", config.mutation_method.value),
        ("mutation_rate", config.mutation_rate),
        ("survival", config.survival_strategy.value),
        ("seed", config.random_seed),
    ]


def write_run_summary(path: Path, config: GAConfig, image_path: str, result: GAResult) -> None:
    settings = [
        ("triangles", config.n_triangles),
        ("generations (max)", config.n_generations),
        ("min_error", config.min_error),
        *_common_settings(config, image_path),
    ]
    results = [
        ("generations run", result.n_generations_run),
        ("stop reason", result.stop_reason),
        ("best fitness", f"{result.best_individual.fitness:.6f}"),
    ]
    _write_summary(path, f"Run: {path.parent.name}", settings, results)


def write_chunked_run_summary(
    path: Path,
    config: GAConfig,
    image_path: str,
    chunk_size: int,
    chunk_generations: int,
    chunked_result,
) -> None:
    fitnesses = [result.best_individual.fitness for result, _ in chunked_result.chunk_results]
    settings = [
        ("chunk_size", chunk_size),
        ("chunk_generations", chunk_generations),
        ("triangles per chunk", config.n_triangles),
        *_common_settings(config, image_path),
    ]
    results = [
        ("chunks", len(chunked_result.chunk_results)),
        ("mean best fitness", f"{sum(fitnesses) / len(fitnesses):.6f}"),
        ("min best fitness", f"{min(fitnesses):.6f}"),
        ("max best fitness", f"{max(fitnesses):.6f}"),
    ]
    _write_summary(path, f"Chunked run: {path.parent.name}", settings, results)


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

        write_run_summary(output_dir / "run_summary.md", config, image_path, result)


if __name__ == "__main__":
    main()
