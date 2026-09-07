"""Report figures/statistics for 4.1–4.6; never launches the GA.

Run: uv run python experiments/analysis.py
The notebook imports these same functions. Saved configs define comparisons.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = "elite_one_point_gene_t50"
GROUPS = {
    "selection": ("4.2 Selection methods", "selection_method"),
    "crossover": ("4.3 Crossover methods", "crossover_method"),
    "triangles": ("4.4 Number of triangles", "n_triangles"),
    "population": ("4.5 Population size", "population_size"),
}


@dataclass
class Run:
    path: Path
    config: dict
    error: float
    fitness: float
    history: np.ndarray
    generations: int
    elapsed: float | None
    stop_reason: str
    ga_elapsed_s: float | None = None

    @property
    def seed(self):
        return self.config["random_seed"]

    @property
    def generation_best(self) -> int:
        """First minimum; generation 0 is the initial population."""
        return int(np.argmin(self.history))


def config_key(config: dict, omit: tuple[str, ...] = ()) -> str:
    return json.dumps({k: v for k, v in config.items()
                       if k not in ("random_seed", *omit)}, sort_keys=True)


def load_runs(results_dir: Path) -> tuple[list[Run], list[str]]:
    """Load raw runs; missing runtime stays missing, never becomes zero."""
    runs, warnings = [], []
    for path in sorted(results_dir.glob("*/seed_*/triangles.json")):
        try:
            data = json.loads(path.read_text())
            config = data["config"]
            for field in ("random_seed", "target_image_path", "n_generations",
                          "mutation_method", "survival_strategy",
                          *(field for _, field in GROUPS.values())):
                if field not in config:
                    raise ValueError(f"missing config field: {field}")
            if config["random_seed"] is None:
                raise ValueError("random_seed is missing")
            history = np.asarray(data["error_history"], dtype=float)
            generations = int(data["n_generations_run"])
            error, fitness = float(data["final_error"]), float(data["final_fitness"])
            if history.ndim != 1 or len(history) != generations + 1 or not len(history):
                raise ValueError("history must include generation 0 and each completed generation")
            if not np.all(np.isfinite(history)) or np.any((history < 0) | (history > 1)):
                raise ValueError("expected finite normalized MSE in [0, 1]")
            if not np.isfinite(error) or not np.isfinite(fitness):
                raise ValueError("non-finite final metric")
            if not np.isclose(error, history[-1], rtol=1e-8, atol=1e-12):
                raise ValueError("final_error differs from last history entry")
            elapsed = data.get("elapsed")
            if elapsed is not None:
                elapsed = float(elapsed)
                if not np.isfinite(elapsed) or elapsed <= 0:
                    warnings.append(f"{path}: invalid runtime treated as missing.")
                    elapsed = None
            ga_elapsed_s = data.get("ga_elapsed_s")
            if ga_elapsed_s is not None:
                ga_elapsed_s = float(ga_elapsed_s)
                if not np.isfinite(ga_elapsed_s) or ga_elapsed_s <= 0:
                    warnings.append(f"{path}: invalid GA runtime treated as missing.")
                    ga_elapsed_s = None
            runs.append(Run(path, config, error, fitness, history, generations,
                            elapsed, data.get("stop_reason", "unknown"), ga_elapsed_s))
        except (KeyError, ValueError, TypeError, OSError) as exc:
            warnings.append(f"Skipped {path}: {exc}")
    unique = {}
    for run in runs:
        key = (config_key(run.config), run.seed)
        if key in unique:
            raise ValueError(f"Duplicate config/seed: {unique[key].path} and {run.path}")
        unique[key] = run
    return runs, warnings


def group_runs(runs: list[Run], baseline: dict, field: str) -> dict:
    """Change one factor only; all other saved settings must match baseline."""
    grouped = {}
    for run in runs:
        if config_key(run.config, (field,)) == config_key(baseline, (field,)):
            grouped.setdefault(run.config[field], []).append(run)
    return dict(sorted(grouped.items()))


def convergence_summary(runs: list[Run]) -> tuple[np.ndarray, np.ndarray]:
    """Median/IQR best-so-far MSE; truncate at the shortest observed history.

    No extrapolation after early stopping or changing sample size along a curve.
    Final population MSE is kept separate: exclusive survival can lose a best.
    """
    length = min(len(run.history) for run in runs)
    histories = np.array([np.minimum.accumulate(r.history)[:length] for r in runs])
    return np.arange(length), np.quantile(histories, [0.25, 0.5, 0.75], axis=0)


def summarize(runs: list[Run], threshold: float | None = None) -> dict:
    errors = np.array([r.error for r in runs])
    times = [r.elapsed for r in runs if r.elapsed is not None]
    ga_times = [r.ga_elapsed_s for r in runs if r.ga_elapsed_s is not None]
    q1, median, q3 = np.quantile(errors, [0.25, 0.5, 0.75])
    row = {
        "runs": len(runs), "median_mse": float(median),
        "mean_mse": float(np.mean(errors)),
        "std_mse": float(np.std(errors, ddof=1)) if len(errors) > 1 else None,
        "iqr_mse": float(q3 - q1) if len(errors) > 1 else None,
        "median_fitness": float(np.median([r.fitness for r in runs])),
        "ga_runtime_runs": len(ga_times),
        "median_ga_runtime_s": float(np.median(ga_times)) if ga_times else None,
        "runtime_runs": len(times),
        "median_runtime_s": float(np.median(times)) if times else None,
        "median_generation_best": float(np.median([r.generation_best for r in runs])),
    }
    if threshold is not None:
        hits = [np.flatnonzero(r.history <= threshold) for r in runs]
        first_hits = [int(h[0]) for h in hits if len(h)]
        row.update(threshold_mse=threshold, threshold_successes=len(first_hits),
                   median_generation_to_threshold=(float(np.median(first_hits))
                                                   if first_hits else None))
    return row


def save_figure(fig, output: Path, name: str) -> str:
    fig.tight_layout()
    for extension in ("png", "pdf"):
        fig.savefig(output / f"{name}.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return f"![{name.replace('_', ' ')}]({name}.png)"


def plot_convergence(groups: dict, output: Path, name: str) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    end = min(len(r.history) for runs in groups.values() for r in runs)
    for label, runs in groups.items():
        x, (q1, median, q3) = convergence_summary(runs)
        line, = ax.plot(x[:end], median[:end], label=f"{label} (n={len(runs)})")
        ax.fill_between(x[:end], q1[:end], q3[:end], color=line.get_color(), alpha=0.18)
    ax.set(xlabel="Generation (0 = initial population)",
           ylabel="Best-so-far normalized MSE ↓", title="Convergence: median and IQR across seeds")
    ax.legend()
    ax.grid(alpha=0.2)
    return save_figure(fig, output, name)


def plot_distribution(groups: dict, output: Path, name: str, runtime=False) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for index, (label, runs) in enumerate(groups.items(), 1):
        values = [r.ga_elapsed_s if runtime else r.error for r in runs]
        values = [v for v in values if v is not None]
        if values:
            ax.boxplot([values], positions=[index], widths=0.45, showfliers=False)
            ax.scatter(index + np.linspace(-0.08, 0.08, len(values)), values,
                       s=24, alpha=0.7, zorder=3)
        else:
            ax.text(index, 0.5, "No GA timing", transform=ax.get_xaxis_transform(), ha="center")
    labels = [f"{label}\n(n={sum(r.ga_elapsed_s is not None for r in runs) if runtime else len(runs)})"
              for label, runs in groups.items()]
    ax.set_xticks(range(1, len(groups) + 1), labels, rotation=15)
    ax.set_xlim(0.5, len(groups) + 0.5)
    ax.set(ylabel="GA runtime (s) ↓" if runtime else "Final normalized MSE ↓",
           title="GA runtime across seeds" if runtime else "Final solution quality and stability")
    ax.grid(axis="y", alpha=0.2)
    return save_figure(fig, output, name)


def plot_images(groups: dict, baseline: dict, output: Path) -> str:
    """Choose the run nearest median final MSE; break ties by seed."""
    fig, axes = plt.subplots(1, len(groups) + 1, figsize=(3 * (len(groups) + 1), 4))
    target = Path(baseline["target_image_path"])
    if not target.is_absolute():
        target = ROOT / target
    panels = [(target, "Target (current file)")]
    for label, runs in groups.items():
        median = np.median([r.error for r in runs])
        representative = min(runs, key=lambda r: (abs(r.error - median), str(r.seed)))
        panels.append((representative.path.parent / "approximation.png",
                       f"{label} triangles · seed {representative.seed}\nMSE {representative.error:.5f}"))
    for ax, (path, title) in zip(axes, panels):
        if path.exists():
            with Image.open(path) as img:
                ax.imshow(img.convert("RGB"))
        else:
            ax.text(0.5, 0.5, "Image unavailable", ha="center", va="center")
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    return save_figure(fig, output, "triangles_images")


def format_value(value) -> str:
    if value is None:
        return "—"
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def markdown_table(rows: list[dict], columns: dict[str, str]) -> str:
    lines = ["| " + " | ".join(columns.values()) + " |",
             "| " + " | ".join(["---"] * len(columns)) + " |"]
    lines.extend("| " + " | ".join(format_value(row.get(k)) for k in columns) + " |" for row in rows)
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict]) -> None:
    if rows:
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


TABLE_COLUMNS = {
    "configuration": "Configuration", "runs": "n", "median_mse": "Median MSE ↓",
    "mean_mse": "Mean MSE ↓", "std_mse": "Sample SD", "iqr_mse": "IQR",
    "median_ga_runtime_s": "Median GA time (s) ↓", "ga_runtime_runs": "GA timed n",
    "median_runtime_s": "Median total time (s)", "runtime_runs": "Total timed n",
    "median_generation_best": "Median gen. of best",
}
DISCUSSION = {
    "selection": "Compare selection pressure and exploration using both the curves and final distributions. "
                 "Do the seeds support the same tendency? These metrics do not directly measure diversity.",
    "crossover": "Compare quality, convergence and spread. Relate observations to how each operator "
                 "preserves or recombines the ordered triangle genes and their drawing order.",
    "triangles": "Compare the MSE improvement with additional runtime and visible differences. "
                 "More triangles increase representational capacity and the search space. "
                 "The displayed run is closest to median final MSE, not chosen as the best-looking image.",
    "population": "Compare quality gains with runtime and convergence. Equal generations are not an equal "
                  "computational budget when population size changes; larger populations process more candidates.",
}


def build_analysis(results_dir: Path = ROOT / "results", output_dir: Path | None = None,
                   baseline_name: str | None = None, expected_runs: int | None = None,
                   threshold: float | None = None) -> Path:
    """Generate report material without launching or changing experiments."""
    results_dir = Path(results_dir).resolve()
    output = Path(output_dir).resolve() if output_dir else results_dir / "analysis"
    manifest_path = results_dir / "campaign.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    baseline_name = baseline_name or manifest.get("baseline", DEFAULT_BASELINE)
    if expected_runs is None:
        expected_runs = len(manifest["seeds"]) if manifest.get("seeds") else 10
    if expected_runs < 1:
        raise ValueError("expected_runs must be positive")
    if threshold is not None and not 0 <= threshold <= 1:
        raise ValueError("threshold must be a normalized MSE in [0, 1]")
    runs, warnings = load_runs(results_dir)
    baseline_runs = [r for r in runs if r.path.parent.parent.name == baseline_name]
    if not baseline_runs:
        raise ValueError(f"No valid baseline runs in {results_dir / baseline_name}")
    if len({config_key(r.config) for r in baseline_runs}) != 1:
        raise ValueError("Baseline directory contains mixed configurations; separate the runs first")
    baseline = baseline_runs[0].config
    output.mkdir(parents=True, exist_ok=True)
    groups = {name: group_runs(runs, baseline, field) for name, (_, field) in GROUPS.items()}
    included = {r.path for group in groups.values() for members in group.values() for r in members}
    for run in runs:
        if run.path not in included:
            warnings.append(f"Excluded {run.path}: settings do not match a one-factor baseline comparison.")
    # The current runner plan is used only for missing-data notices, never as
    # a replacement for metadata saved with an existing run.
    from experiments.experiments import EXPERIMENTS

    planned_experiments = manifest.get("experiments", EXPERIMENTS)
    unique_groups = {}
    baseline_seeds = {r.seed for r in baseline_runs}
    for name, group in groups.items():
        runner_field = {"selection": "selection", "crossover": "crossover",
                        "triangles": "triangles", "population": "population_size"}[name]
        planned = {cfg[runner_field] for cfg in planned_experiments.get(name, []) if runner_field in cfg}
        if planned - set(group):
            warnings.append(f"{name}: missing planned values {sorted(planned - set(group))}.")
        if len(group) < 2:
            warnings.append(f"{name}: only baseline data; no parameter comparison is possible.")
        for label, members in group.items():
            unique_groups[config_key(members[0].config)] = members
            if len(members) != expected_runs:
                warnings.append(f"{name}/{label}: {len(members)} runs available; planned count is {expected_runs}.")
            if {r.seed for r in members} != baseline_seeds:
                warnings.append(f"{name}/{label}: seed set differs from baseline; comparisons are unpaired.")
    if any(r.ga_elapsed_s is None for r in runs if r.path in included):
        warnings.append("Some GA timings are missing (including legacy runs). GA plots and speed ranking "
                        "never substitute total runtime; timed sample sizes are reported separately.")
    if any(r.elapsed is None for r in runs if r.path in included):
        warnings.append("Some runtimes are missing; timed sample sizes are reported separately.")
    if len({len(r.history) for r in runs if r.path in included}) > 1:
        warnings.append("History lengths differ: curves stop at the shortest run in each comparison.")
    if baseline["n_generations"] <= 5:
        warnings.append("The saved generation budget is at most 5: treat these as smoke-test data.")
    if any(r.error > np.min(r.history) + 1e-12 for r in runs if r.path in included):
        warnings.append("Some runs lost earlier best solutions: final MSE describes the returned final "
                        "population, while convergence shows best-so-far MSE.")

    lines = ["# 4. Experiments & Results", "Generated descriptive results and discussion prompts. "
             "Complete the interpretation after the full experiment campaign.",
             "## 4.1 Experimental setup",
             "Three questions: **quality** (final MSE), **speed** (runtime and convergence), "
             "and **stability** (variation across independent seeds).",
             f"Baseline directory: `{baseline_name}`. Planned runs/configuration: **{expected_runs}**. "
             f"Observed baseline seeds: `{sorted(baseline_seeds)}`.",
             "Saved baseline configuration (the random seed varies):",
             "```json\n" + json.dumps({k: v for k, v in baseline.items() if k != "random_seed"}, indent=2) + "\n```",
             "MSE is averaged over RGB channels after dividing pixel values by 255, so it lies in [0, 1]. "
             "Lower is better. Fitness is 1/(1 + MSE); per-run fitness is exported to CSV.",
             "Each comparison changes one saved setting relative to the same baseline. Baseline runs are reused "
             "across sections and counted once in the overall comparison.",
             "Curves show median best-so-far MSE with IQR (25th–75th percentile), not a confidence interval. "
             "Generation 0 is initialization. SD uses n−1; SD and IQR are omitted for a single run.",
             "GA time (`ga_elapsed_s`) measures only `run_ga`, including initialization and fitness evaluation. "
             "Total time (`elapsed`) includes subprocess startup, image loading, GA, plotting and file output. "
             "These are separate metrics; legacy runs have no GA timing. No generation timestamps or evaluation counts were saved, so "
             "time-to-target and equal-evaluation convergence cannot be reconstructed.",
             "Generation of best is the first minimum observed MSE. A small value can indicate an early plateau "
             "at poor quality, so it is not a speed ranking by itself.",
             "Record hardware, software revision, target image dimensions and execution conditions for "
             "the full campaign. New runner outputs store target_sha256; legacy runs lack that hash.",
             "### Data coverage", "\n".join(f"- {w}" for w in warnings) or "All detected comparisons meet the requested run count."]
    if threshold is not None:
        lines.append(f"Common target: normalized MSE ≤ {threshold:g}. Threshold tables report successes/all "
                     "runs and median first-hit generation among successes only. Failures are not zero-generation "
                     "hits. Choose the target before comparing outcomes.")
    rows = []
    for name, (heading, field) in GROUPS.items():
        group = groups[name]
        lines.append(f"## {heading}")
        if len(group) < 2:
            lines.append("**Incomplete comparison: only baseline data are available.**")
        if name in ("selection", "crossover"):
            lines.append(plot_convergence(group, output, f"{name}_convergence"))
        lines.append(plot_distribution(group, output, f"{name}_mse"))
        if name in ("triangles", "population"):
            lines.append(plot_distribution(group, output, f"{name}_runtime", runtime=True))
        if name == "triangles":
            lines.append(plot_images(group, baseline, output))
        if name == "population":
            lines.append(plot_convergence(group, output, f"{name}_convergence"))
        section_rows = [{"experiment": name, "configuration": label, **summarize(members, threshold)}
                        for label, members in group.items()]
        rows.extend(section_rows)
        lines.append(markdown_table(section_rows, TABLE_COLUMNS))
        if threshold is not None:
            lines.append(markdown_table(section_rows, {"configuration": "Configuration", "runs": "n",
                         "threshold_successes": "Reached target", "median_generation_to_threshold": "Median gen. (successes only)"}))
        lines.extend(["**Analysis prompts:** " + DISCUSSION[name],
                      "Write your interpretation here, citing measured differences and uncertainty."])

    lines.append("## 4.6 Overall comparison")
    overall = [{"configuration": members[0].path.parent.parent.name, **summarize(members, threshold)}
               for members in unique_groups.values()]
    lines.append(markdown_table(overall, TABLE_COLUMNS))
    for label, metric in [("Quality: lowest median final MSE", "median_mse"),
                          ("Speed: lowest median GA runtime", "median_ga_runtime_s"),
                          ("Stability: lowest final-MSE IQR", "iqr_mse")]:
        eligible = [row for row in overall if row[metric] is not None and
                    (metric != "median_ga_runtime_s" or row["ga_runtime_runs"] == row["runs"])]
        if eligible:
            value = min(row[metric] for row in eligible)
            winners = [str(row["configuration"]) for row in eligible if row[metric] == value]
            lines.append(f"- {label}: **{', '.join(winners)}** ({format_value(value)}).")
        else:
            lines.append(f"- {label}: insufficient measurements.")
    lines.extend(["These are descriptive leaders among available configurations, not evidence of a universal "
                  "winner or statistical significance. See coverage warnings before drawing conclusions. "
                  "Low variability can mean consistently poor results; assess stability alongside quality.",
                  "**Analysis prompts:** Which configuration suits each objective? How large are quality gains "
                  "relative to runtime and seed variation? Combining preferred settings from individual-factor "
                  "experiments requires a separate validation experiment."])
    write_csv(output / "configuration_summary.csv", rows)
    write_csv(output / "overall_summary.csv", overall)
    per_run = []
    for members in unique_groups.values():
        for run in members:
            per_run.append({"configuration": run.path.parent.parent.name, "seed": run.seed,
                            "final_mse": run.error, "final_fitness": run.fitness,
                            "best_observed_mse": float(np.min(run.history)),
                            "generation_best": run.generation_best, "generations_run": run.generations,
                            "runtime_s": run.elapsed, "ga_elapsed_s": run.ga_elapsed_s,
                            "stop_reason": run.stop_reason, "source": str(run.path),
                            "saved_config": json.dumps(run.config, sort_keys=True)})
    write_csv(output / "runs.csv", per_run)
    report = output / "analysis.md"
    report.write_text("\n\n".join(lines) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--baseline", help="Baseline directory name (default: campaign.json, or legacy baseline)")
    parser.add_argument("--expected-runs", type=int, help="Expected runs (default: campaign seeds, or 10 for legacy data)")
    parser.add_argument("--mse-threshold", type=float, help="Optional common quality target in [0, 1]")
    args = parser.parse_args()
    try:
        report = build_analysis(args.results_dir, args.output_dir, args.baseline,
                                args.expected_runs, args.mse_threshold)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Analysis written to {report}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    main()
