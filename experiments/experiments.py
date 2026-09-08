"""Run isolated experiment campaigns; use --dry-run to inspect the plan.

Defaults remain a small smoke test until the pilot budget has been chosen.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

from ga_triangles.cli import build_arg_parser, config_from_args
from ga_triangles.config import MutationMethod, SelectionMethod

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "data/skrik.png"
GENERATIONS = 5
POPULATION = 10
SEEDS = [42, 123]
RESULTS_DIR = ROOT / "results" / "full_campaign"
BASELINE = {
    "selection": "elite", "crossover": "one_point", "mutation": "gene",
    "triangles": 50, "survival": "additive", "population_size": POPULATION,
    "mutation_rate": 0.05, "crossover_rate": 0.9,
}


def experiment_plan(baseline: dict, population_sizes=(50, 100, 200)) -> dict:
    return {
        "selection": [{**baseline, "selection": value}
                      for value in (method.value for method in SelectionMethod)],
        "crossover": [{**baseline, "crossover": value} for value in ("two_point", "uniform")],
        "triangles": [{**baseline, "triangles": value} for value in (20, 100)],
        "population": [{**baseline, "population_size": value} for value in population_sizes],
        "survival": [{**baseline, "survival": value} for value in ("additive", "exclusive")],
        "mutation": [{**baseline, "mutation": method.value} for method in MutationMethod],
    }


EXPERIMENTS = experiment_plan(BASELINE)


def cli_arguments(cfg: dict, seed: int | None, image: str, generations: int) -> list[str]:
    args = ["--image", image, "--generations", str(generations)]
    for field, flag in (("triangles", "triangles"), ("population_size", "population-size"),
                        ("selection", "selection"), ("crossover", "crossover"),
                        ("mutation", "mutation"), ("survival", "survival"),
                        ("mutation_rate", "mutation-rate"), ("crossover_rate", "crossover-rate")):
        args.extend([f"--{flag}", str(cfg[field])])
    if seed is not None:
        args.extend(["--seed", str(seed)])
    return args


def saved_config(cfg: dict, seed: int | None, image: str, generations: int) -> dict:
    """Include CLI defaults too, so cache validation covers all GA settings."""
    args = build_arg_parser().parse_args(cli_arguments(cfg, seed, image, generations))
    return json.loads(json.dumps(asdict(config_from_args(args))))


def config_name(config: dict, image_sha256: str) -> str:
    """Readable settings plus a digest of every effective setting and target bytes."""
    settings = {k: v for k, v in config.items() if k != "random_seed"}
    identity = json.dumps([settings, image_sha256], sort_keys=True).encode()
    digest = hashlib.sha256(identity).hexdigest()[:12]
    return (f"{config['selection_method']}_{config['crossover_method']}_{config['mutation_method']}"
            f"_t{config['n_triangles']}_p{config['population_size']}_g{config['n_generations']}_{digest}")


def validate_result(data: dict, expected: dict, path: Path) -> None:
    """Refuse stale or incomplete records instead of silently reusing them."""
    if data.get("config") != expected:
        raise ValueError(f"Saved settings differ from requested settings: {path}. Use a new campaign directory.")
    try:
        count = data["n_generations_run"]
        errors, fitnesses = data["error_history"], data["fitness_history"]
        if (type(count) is not int or count != expected["n_generations"]
                or len(errors) != count + 1 or len(fitnesses) != count + 1):
            raise ValueError("incomplete history or generation budget")
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in errors):
            raise ValueError("invalid MSE history")
        if not all(math.isfinite(v) for v in fitnesses):
            raise ValueError("invalid fitness history")
        if (not math.isclose(data["final_error"], errors[-1])
                or not math.isclose(data["final_fitness"], fitnesses[-1])):
            raise ValueError("final metrics differ from history")
        if not math.isfinite(data["ga_elapsed_s"]) or data["ga_elapsed_s"] <= 0:
            raise ValueError("missing or invalid GA timing")
        if not data["stop_reason"]:
            raise ValueError("missing stop reason")
        triangles = data["triangles"]
        if not isinstance(triangles, list) or len(triangles) != expected["n_triangles"]:
            raise ValueError("missing or incorrect triangle count")
        for triangle in triangles:
            vertices, color = triangle["vertices"], triangle["color"]
            if len(vertices) != 3 or any(len(point) != 2 for point in vertices) or len(color) != 4:
                raise ValueError("triangles require three (x, y) vertices and RGBA colour")
            if not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1
                       for v in [*(v for point in vertices for v in point), *color]):
                raise ValueError("triangle coordinates and colours must be numbers in [0, 1]")
        canvas = data["canvas"]
        if any(type(canvas[k]) is not int or canvas[k] <= 0 for k in ("width", "height")):
            raise ValueError("invalid canvas dimensions")
        background = canvas["background_rgb"]
        if len(background) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in background):
            raise ValueError("invalid canvas background")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValueError(f"Incomplete/invalid result {path}: {exc}. Use a new campaign directory.") from exc
    for name in ("approximation.png", "fitness.png"):
        if not (path.parent / name).is_file():
            raise ValueError(f"Missing output {path.parent / name}; use a new campaign directory.")


def write_json(path: Path, data: dict) -> None:
    """Replace metadata atomically so an interrupted write does not truncate it."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def run_single(cfg: dict, seed: int, *, results_dir: Path = RESULTS_DIR,
               image: str = IMAGE, generations: int = GENERATIONS) -> dict:
    image_path = Path(image)
    if not image_path.is_absolute():
        image_path = ROOT / image_path
    image = str(image_path.resolve())
    image_sha256 = hashlib.sha256(image_path.read_bytes()).hexdigest()
    expected = saved_config(cfg, seed, image, generations)
    name = config_name(expected, image_sha256)
    out_dir = Path(results_dir).resolve() / name / f"seed_{seed}"
    result_file = out_dir / "triangles.json"
    if result_file.exists():
        data = json.loads(result_file.read_text())
        validate_result(data, expected, result_file)
        if data.get("target_sha256") != image_sha256:
            raise ValueError(f"Target hash mismatch: {result_file}. Use a new campaign directory.")
        elapsed = data.get("elapsed")
        if not isinstance(elapsed, (float, int)) or not math.isfinite(elapsed) or elapsed <= 0:
            raise ValueError(f"Missing/invalid total timing: {result_file}. Use a new campaign directory.")
        print(f"Skipping {name}, seed={seed}: settings, target and outputs verified.")
        return data

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "ga_triangles.cli",
           *cli_arguments(cfg, seed, image, generations), "--output-dir", str(out_dir)]
    print(f"Running {name}, seed={seed}...", flush=True)
    start = time.perf_counter()
    subprocess.run(cmd, check=True, cwd=ROOT)
    elapsed = time.perf_counter() - start
    data = json.loads(result_file.read_text())
    validate_result(data, expected, result_file)
    if hashlib.sha256(image_path.read_bytes()).hexdigest() != image_sha256:
        raise ValueError("Target changed during the run; use a new campaign directory.")
    data.update(elapsed=elapsed, target_sha256=image_sha256)
    write_json(result_file, data)
    return data


def write_summary(results_dir: Path) -> None:
    rows = []
    for path in sorted(results_dir.glob("*/seed_*/triangles.json")):
        data = json.loads(path.read_text())
        rows.append([path.parent.parent.name, data["config"]["random_seed"],
                     data["final_error"], data.get("ga_elapsed_s"), data.get("elapsed"),
                     data["n_generations_run"]])
    headers = ["Configuration", "Seed", "Final MSE", "GA time (s)", "Total time (s)", "Generations"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join("—" if v is None else str(v) for v in row) + " |" for row in rows)
    (results_dir / "summary.md").write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=IMAGE)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--generations", type=int, default=GENERATIONS)
    parser.add_argument("--population-size", type=int, default=POPULATION)
    parser.add_argument("--population-sizes", type=int, nargs="+", default=[50, 100, 200])
    parser.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    parser.add_argument("--experiment", choices=["baseline", "all", *EXPERIMENTS], default="baseline")
    parser.add_argument("--dry-run", action="store_true", help="Print planned runs; write nothing and do not run GA")
    args = parser.parse_args(argv)
    if args.generations < 1 or any(p < 2 or p % 2 for p in [args.population_size, *args.population_sizes]):
        parser.error("Use positive generations and even population sizes >= 2 (parents are paired).")
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        parser.error("Seeds must be distinct, non-negative integers.")
    baseline = {**BASELINE, "population_size": args.population_size}
    plan = experiment_plan(baseline, args.population_sizes)
    image = Path(args.image)
    image = (ROOT / image).resolve() if not image.is_absolute() else image.resolve()
    results_dir = args.results_dir.resolve()
    try:
        image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
        baseline_config = saved_config(baseline, None, str(image), args.generations)
        baseline_name = config_name(baseline_config, image_hash)
        manifest = {"baseline": baseline_name, "baseline_config": baseline_config,
                    "seeds": args.seeds, "target_sha256": image_hash, "experiments": plan}
        manifest_path = results_dir / "campaign.json"
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
            raise ValueError(f"Campaign settings differ from {manifest_path}. Choose a new --results-dir.")
        configs = [baseline]
        if args.experiment == "all":
            configs.extend(cfg for group in plan.values() for cfg in group)
        elif args.experiment != "baseline":
            configs.extend(plan[args.experiment])
        unique = {config_name(saved_config(cfg, None, str(image), args.generations), image_hash): cfg
                  for cfg in configs}
        print(f"Campaign: {results_dir}\nBaseline: {baseline_name}\n"
              f"{len(unique)} configurations × {len(args.seeds)} seeds = {len(unique) * len(args.seeds)} runs")
        if args.dry_run:
            for name in unique:
                print(f"  {name}: seeds {args.seeds}")
            return
        results_dir.mkdir(parents=True, exist_ok=True)
        write_json(manifest_path, manifest)
        total = len(unique) * len(args.seeds)
        completed = 0
        print(f"Fremdrift: {completed}/{total} fullført | {total} gjenstår", flush=True)
        for cfg in unique.values():
            for seed in args.seeds:
                run_single(cfg, seed, results_dir=results_dir, image=str(image), generations=args.generations)
                # Count new runs and successfully validated cached results only.
                completed += 1
                print(f"Fremdrift: {completed}/{total} fullført | {total - completed} gjenstår",
                      flush=True)
        write_summary(results_dir)
        print(f"Done. Analyse with: uv run python experiments/analysis.py --results-dir '{results_dir}'")
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
