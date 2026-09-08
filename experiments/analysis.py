"""Report figures/statistics for 4.1–4.8; never launches the GA.

Run: uv run python experiments/analysis.py
The notebook imports these same functions. Saved configs define comparisons.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = "elite_one_point_gene_t50"
GROUPS = {
    "selection": ("4.2 Selection methods", "selection_method"),
    "crossover": ("4.3 Crossover methods", "crossover_method"),
    "triangles": ("4.4 Number of triangles", "n_triangles"),
    "population": ("4.5 Population size", "population_size"),
    "survival": ("4.6 Survival strategies", "survival_strategy"),
    "mutation": ("4.7 Mutation methods", "mutation_method"),
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


def convergence_summary(runs: list[Run], *, best_so_far: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Median/IQR MSE; truncate at the shortest observed history.

    No extrapolation after early stopping or changing sample size along a curve.
    Use best_so_far=False to show current-generation best, including losses.
    """
    length = min(len(run.history) for run in runs)
    histories = np.array([(np.minimum.accumulate(r.history) if best_so_far else r.history)[:length]
                          for r in runs])
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


def display_label(value) -> str:
    names = {
        "elite": "Elite", "roulette": "Roulette", "ranking": "Ranking",
        "tournament_deterministic": "Deterministic tournament",
        "tournament_probabilistic": "Probabilistic tournament",
        "one_point": "One-point", "two_point": "Two-point", "uniform": "Uniform",
    }
    return names.get(value, str(value).replace("_", " ").capitalize())


def plot_context(config: dict, experiment: str | None = None) -> str:
    parts = [f"Target: {Path(config['target_image_path']).name}",
             f"Budget: {config['n_generations']} generations"]
    if experiment != "triangles":
        parts.append(f"{config['n_triangles']} triangles")
    if experiment != "population":
        parts.append(f"Population: {config['population_size']}")
    if experiment != "selection":
        parts.append(f"Selection: {display_label(config['selection_method'])}")
    if experiment != "crossover":
        parts.append(f"Crossover: {display_label(config['crossover_method'])}")
    if experiment == "mutation":
        parts.append(f"Mutation rate: {config['mutation_rate']:g}")
        parts.append(f"Survival: {display_label(config['survival_strategy'])}")
    return " | ".join(parts)


def save_figure(fig, output: Path, name: str, *, title: str,
                question: str, context: str, guide: str) -> str:
    """Give every standalone figure its experiment, question and reading guide."""
    fig.text(0.07, 0.97, title, fontsize=16, weight="bold", va="top")
    fig.text(0.07, 0.92, question, fontsize=12, va="top")
    fig.text(0.07, 0.87, textwrap.fill(context, 115), fontsize=9, color="#555555", va="top")
    fig.text(0.07, 0.025, textwrap.fill(guide, 125), fontsize=10, color="#333333", va="bottom")
    fig.tight_layout(rect=(0.02, 0.13, 0.99, 0.80))
    for extension in ("png", "pdf"):
        fig.savefig(output / f"{name}.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return f"![{title}]({name}.png)\n\n{guide}"


def style_axis(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)


def plot_convergence(groups: dict, output: Path, name: str, experiment: str) -> str:
    fig, ax = plt.subplots(figsize=(10, 7))
    best_so_far = experiment != "survival"
    end = min(len(r.history) for runs in groups.values() for r in runs)
    for label, runs in groups.items():
        x, (q1, median, q3) = convergence_summary(runs, best_so_far=best_so_far)
        line, = ax.plot(x[:end], median[:end], linewidth=2,
                       label=f"{display_label(label)} (n={len(runs)})")
        ax.fill_between(x[:end], q1[:end], q3[:end], color=line.get_color(), alpha=0.15)
    ax.set(xlabel="Generation (0 = initial population)",
           ylabel="Best-so-far MSE (lower is better)" if best_so_far else
                  "Current-generation best MSE (lower is better)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(frameon=False, fontsize=10, ncol=2 if len(groups) > 4 else 1)
    style_axis(ax)
    question = {
        "selection": "Which selection method reduces image error fastest?",
        "crossover": "Which crossover method reduces image error fastest?",
        "mutation": "Which mutation method reduces image error fastest?",
        "population": "How does population size affect progress per generation?",
        "survival": "How does allowing parents to survive affect solution quality over generations?",
    }[experiment]
    return save_figure(fig, output, name,
                       title=f"{GROUPS[experiment][0]} — convergence", question=question,
                       context=plot_context(next(iter(groups.values()))[0].config, experiment),
                       guide="Each colour is one configuration. Line = median across seeds; shading = middle 50% (IQR), "
                             "not a confidence interval. Lower curves mean better solutions at that generation. "
                             "n = number of runs; generation speed is not wall-clock speed. "
                             + ("" if best_so_far else "Current-generation best, not best-so-far: increases reveal "
                                "lost quality; the median can hide losses in individual runs."))


def plot_distribution(groups: dict, output: Path, name: str, experiment: str, runtime=False) -> str:
    fig, ax = plt.subplots(figsize=(max(10, 1.9 * len(groups)), 7))
    for index, (label, runs) in enumerate(groups.items(), 1):
        values = [r.ga_elapsed_s if runtime else r.error for r in runs]
        values = [v for v in values if v is not None]
        color = plt.get_cmap("tab10")((index - 1) % 10)
        if values:
            if len(values) > 1:
                ax.boxplot([values], positions=[index], widths=0.45, showfliers=False,
                           patch_artist=True, boxprops={"facecolor": color, "alpha": 0.2},
                           medianprops={"color": color, "linewidth": 2})
            offsets = np.linspace(-0.08, 0.08, len(values)) if len(values) > 1 else [0]
            ax.scatter(index + np.asarray(offsets), values, color=color, s=35, zorder=3)
        else:
            ax.text(index, 0.5, "No GA timing", transform=ax.get_xaxis_transform(), ha="center")
    labels = [f"{textwrap.fill(display_label(label), 20)}\n"
              f"n={sum(r.ga_elapsed_s is not None for r in runs) if runtime else len(runs)}"
              for label, runs in groups.items()]
    ax.set_xticks(range(1, len(groups) + 1), labels)
    ax.set_xlim(0.5, len(groups) + 0.5)
    ax.set(xlabel={"selection": "Selection method", "crossover": "Crossover method",
                   "triangles": "Number of triangles", "population": "Population size",
                   "survival": "Survival strategy", "mutation": "Mutation method"}[experiment],
           ylabel="GA runtime (seconds; lower is faster)" if runtime else "Final MSE (lower is better)")
    style_axis(ax)
    question = ({"triangles": "How much computation does increasing the triangle count cost?",
                 "population": "How much computation does increasing the population cost?"}[experiment]
                if runtime else {
                    "selection": "Which selection method gives low and consistent final error?",
                    "crossover": "Which crossover method gives low and consistent final error?",
                    "mutation": "Which mutation method gives low and consistent final error?",
                    "triangles": "Does increasing the triangle count improve final image quality?",
                    "population": "Does increasing population size improve final image quality?",
                    "survival": "Which survival strategy gives low and consistent final error?",
                }[experiment])
    return save_figure(fig, output, name,
                       title=f"{GROUPS[experiment][0]} — {'computational cost' if runtime else 'quality and stability'}",
                       question=question, context=plot_context(next(iter(groups.values()))[0].config, experiment),
                       guide="Each dot is one run (seed). Box = middle 50%; line inside = median. "
                             "Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. "
                             + ("Compare typical runtime and its spread." if runtime else
                                "Lower boxes indicate better quality; shorter boxes indicate less variation."))


def target_path(baseline: dict) -> Path:
    path = Path(baseline["target_image_path"])
    return path if path.is_absolute() else ROOT / path


def plot_image_panels(panels: list, baseline: dict, output: Path, name: str,
                      title: str, question: str, guide: str, experiment=None) -> str:
    columns = min(4, len(panels))
    rows = (len(panels) + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, squeeze=False, figsize=(12, 3 * rows + 3))
    for ax in axes.flat:
        ax.axis("off")
    for ax, (path, label) in zip(axes.flat, panels):
        if path.exists():
            with Image.open(path) as img:
                ax.imshow(img.convert("RGB"))
        else:
            ax.text(0.5, 0.5, "Image unavailable", ha="center", va="center")
        ax.set_title(label, fontsize=11, pad=10)
    return save_figure(fig, output, name, title=title, question=question,
                       context=plot_context(baseline, experiment), guide=guide)


def plot_images(groups: dict, baseline: dict, output: Path) -> str:
    """Choose the run nearest median final MSE; break ties by seed."""
    panels = [(target_path(baseline), "Target (current file)")]
    for label, runs in groups.items():
        median = np.median([r.error for r in runs])
        representative = min(runs, key=lambda r: (abs(r.error - median), str(r.seed)))
        panels.append((representative.path.parent / "approximation.png",
                       f"{label} triangles · seed {representative.seed}\nMSE {representative.error:.5f}"))
    return plot_image_panels(panels, baseline, output, "4_4_triangles_images",
                             "4.4 Number of triangles — visual quality",
                             "What visual detail is gained by using more triangles?",
                             "Each configuration shows the run closest to its median final MSE. "
                             "Compare shapes, colours and detail with the target; MSE alone does not measure recognizability.",
                             experiment="triangles")


def baseline_overview(runs: list[Run], output: Path) -> list[str]:
    """Explain repetitions of the baseline separately from parameter experiments."""
    runs = sorted(runs, key=lambda run: run.seed)
    baseline = runs[0].config
    fig, ax = plt.subplots(figsize=(10, 7))
    for run in runs:
        ax.plot(np.minimum.accumulate(run.history), label=f"Seed {run.seed}", linewidth=1.8)
    ax.set(xlabel="Generation (0 = initial population)", ylabel="Best-so-far MSE (lower is better)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(frameon=False, ncol=2 if len(runs) > 5 else 1)
    style_axis(ax)
    curve = save_figure(fig, output, "4_1_baseline_seed_convergence",
                        title="4.1 Baseline check — progress across seeds",
                        question="Does the baseline keep improving within the generation budget?",
                        context=plot_context(baseline),
                        guide="Each line is a different seed using the SAME configuration, not a different method. "
                              "A falling line means improvement; a flat line means no new best solution. "
                              "Separated lines show variation between runs.")
    panels = [(target_path(baseline), "Target (current file)")]
    panels.extend((run.path.parent / "approximation.png", f"Seed {run.seed}\nFinal MSE {run.error:.5f}")
                  for run in runs)
    images = plot_image_panels(panels, baseline, output, "4_1_baseline_seed_images",
                               "4.1 Baseline check — generated images",
                               "How recognizable is the target after the same generation budget?",
                               "All available baseline seeds are shown. They use the same settings; "
                               "differences arise from the random run. Compare the visible shapes and colours as well as MSE.")
    rows = [{"seed": run.seed, "initial_mse": float(run.history[0]), "final_mse": run.error,
             "ga_time": run.ga_elapsed_s, "generation_best": run.generation_best} for run in runs]
    table = markdown_table(rows, {"seed": "Seed", "initial_mse": "Initial MSE",
                                 "final_mse": "Final MSE ↓", "ga_time": "GA time (s)",
                                 "generation_best": "First gen. of best"})
    return ["### Baseline check: understand the repeated runs first",
            "The baseline figures compare seeds of one configuration. They do not compare selection methods, "
            "crossovers, mutations, survival strategies, triangle counts or populations. "
            "Those comparisons appear below only when alternatives have been run.",
            curve, table, images]


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
    "survival": "Compare additive (parents and offspring compete) with exclusive (only offspring survive). "
                "Does retaining parents improve final quality and consistency? Compare median GA time too. "
                "These curves show current-generation best MSE: exclusive may lose an earlier best solution. "
                "The median can hide individual losses; inspect per-seed histories and best_observed_mse in runs.csv. "
                "These measurements do not establish population diversity.",
    "mutation": "Compare convergence, final quality, seed variation and GA runtime with all other settings fixed. "
                "The same numerical mutation rate does not imply the same amount of mutation: gene can change "
                "one triangle per individual; multigene tests a random subset; uniform tests every triangle; "
                "complete perturbs every triangle when triggered for an individual. Each selected triangle has "
                "one coordinate or colour component changed. Relate results to these differences without "
                "claiming that diversity was measured directly.",
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
                        "triangles": "triangles", "population": "population_size", "survival": "survival",
                        "mutation": "mutation"}[name]
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
                        "population. Survival curves show current-generation best MSE; other convergence "
                        "comparisons show best-so-far MSE.")

    lines = ["# 4. Experiments & Results", "Generated descriptive results and discussion prompts. "
             "Complete the interpretation after the full experiment campaign.",
             "## 4.1 Experimental setup",
             "Three questions: **quality** (final MSE), **speed** (runtime and convergence), "
             "and **stability** (variation across independent seeds).",
             f"Baseline directory: `{baseline_name}`. Planned runs/configuration: **{expected_runs}**. "
             f"Observed baseline seeds: `{sorted(baseline_seeds)}`.",
             "The main experiment budget means the resources chosen for the final comparisons: "
             "a fixed generation limit per run and a planned number of seeds per configuration. "
             "Population size is fixed except in its own experiment. This is not a runtime limit "
             "and does not guarantee that the GA has converged.",
             "Saved baseline configuration (the random seed varies):",
             "```json\n" + json.dumps({k: v for k, v in baseline.items() if k != "random_seed"}, indent=2) + "\n```",
             "MSE is averaged over RGB channels after dividing pixel values by 255, so it lies in [0, 1]. "
             "Lower is better. Fitness is 1/(1 + MSE); per-run fitness is exported to CSV.",
             "Each comparison changes one saved setting relative to the same baseline. Baseline runs are reused "
             "across sections and counted once in the overall comparison.",
             "Curves show median best-so-far MSE with IQR (25th–75th percentile), not a confidence interval. "
             "Exception: survival curves show current-generation best MSE so losses remain visible. "
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
    lines.extend(baseline_overview(baseline_runs, output))
    rows = []
    for name, (heading, field) in GROUPS.items():
        group = groups[name]
        lines.append(f"## {heading}")
        section_rows = [{"experiment": name, "configuration": label, **summarize(members, threshold)}
                        for label, members in group.items()]
        rows.extend(section_rows)
        if len(group) < 2:
            lines.append("**Not yet available: only the baseline has been run for this factor.** "
                         "See the baseline figures in 4.1. A comparison figure will appear here once at least "
                         "two values of this factor are available.")
            lines.append("**Question for this experiment:** " + DISCUSSION[name])
            continue
        prefix = heading.split()[0].replace(".", "_") + "_" + name
        if name in ("selection", "crossover", "survival", "mutation"):
            lines.append(plot_convergence(group, output, f"{prefix}_convergence", name))
        lines.append(plot_distribution(group, output, f"{prefix}_final_mse", name))
        if name in ("triangles", "population"):
            lines.append(plot_distribution(group, output, f"{prefix}_ga_runtime", name, runtime=True))
        if name == "triangles":
            lines.append(plot_images(group, baseline, output))
        if name == "population":
            lines.append(plot_convergence(group, output, f"{prefix}_convergence", name))
        lines.append(markdown_table(section_rows, TABLE_COLUMNS))
        if threshold is not None:
            lines.append(markdown_table(section_rows, {"configuration": "Configuration", "runs": "n",
                         "threshold_successes": "Reached target", "median_generation_to_threshold": "Median gen. (successes only)"}))
        lines.extend(["**Analysis prompts:** " + DISCUSSION[name],
                      "Write your interpretation here, citing measured differences and uncertainty."])

    lines.append("## 4.8 Overall comparison")
    overall = [{"configuration": members[0].path.parent.parent.name, **summarize(members, threshold)}
               for members in unique_groups.values()]
    lines.append(markdown_table(overall, TABLE_COLUMNS))
    for label, metric in [("Quality: lowest median final MSE", "median_mse"),
                          ("Speed: lowest median GA runtime", "median_ga_runtime_s"),
                          ("Stability: lowest final-MSE IQR", "iqr_mse")]:
        if len(overall) < 2:
            lines.append(f"- {label}: no comparison yet; only baseline results are available.")
            continue
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
