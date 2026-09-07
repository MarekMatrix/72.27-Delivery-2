# experiments/analysis.py
import json
from pathlib import Path
import matplotlib.pyplot as plt

RESULTS_DIR = Path("results")

EXPERIMENT_GROUPS = {
    "selection": [
        "elite_one_point_gene_t50",
        "tournament_deterministic_one_point_gene_t50",
        "roulette_one_point_gene_t50",
        "ranking_one_point_gene_t50",
    ],
    "crossover": [
        "elite_one_point_gene_t50",
        "elite_two_point_gene_t50",
        "elite_uniform_gene_t50",
    ],
    "triangles": [
        "elite_one_point_gene_t20",
        "elite_one_point_gene_t50",
        "elite_one_point_gene_t100",
    ],
}


def load_results(config_name: str) -> list[dict]:
    """Load all seed results for a given config name. Returns empty list if not found."""
    config_dir = RESULTS_DIR / config_name
    if not config_dir.exists():
        return []
    runs = []
    for seed_dir in sorted(config_dir.iterdir()):
        result_file = seed_dir / "triangles.json"
        if result_file.exists():
            with open(result_file) as f:
                runs.append(json.load(f))
    return runs


def plot_boxplot(config_names: list[str], title: str, out_path: str):
    """Box plot of final fitness across seeds for each configuration."""
    data = []
    labels = []
    for name in config_names:
        runs = load_results(name)
        if not runs:
            continue
        fitnesses = [r["final_fitness"] for r in runs]
        data.append(fitnesses)
        labels.append(name.replace("_", "\n"))

    if not data:
        print(f"  Skipping {title} — no data found")
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot(data, tick_labels=labels)
    ax.set_title(title)
    ax.set_ylabel("Final fitness")
    ax.set_xlabel("Configuration")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


def plot_convergence(config_names: list[str], title: str, out_path: str):
    """Fitness curves for the best seed of each configuration."""
    fig, ax = plt.subplots(figsize=(10, 5))
    plotted = False
    for name in config_names:
        runs = load_results(name)
        if not runs:
            continue
        best_run = max(runs, key=lambda r: r["final_fitness"])
        ax.plot(best_run["fitness_history"], label=name)
        plotted = True

    if not plotted:
        print(f"  Skipping {title} — no data found")
        plt.close()
        return

    ax.set_title(title)
    ax.set_ylabel("Best fitness")
    ax.set_xlabel("Generation")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


if __name__ == "__main__":
    Path("results/plots").mkdir(parents=True, exist_ok=True)
    for exp_name, configs in EXPERIMENT_GROUPS.items():
        plot_boxplot(
            configs,
            title=f"Final fitness — {exp_name}",
            out_path=f"results/plots/boxplot_{exp_name}.png",
        )
        plot_convergence(
            configs,
            title=f"Convergence — {exp_name}",
            out_path=f"results/plots/convergence_{exp_name}.png",
        )