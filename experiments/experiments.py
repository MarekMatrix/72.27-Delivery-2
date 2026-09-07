# experiments/run_experiments.py
import subprocess
import json
import time
from pathlib import Path

IMAGE = "data/skrik.png"
GENERATIONS = 5
POPULATION = 10
SEEDS = [42, 123] #[42, 123, 456, 789, 1337]
RESULTS_DIR = Path("results")
BASELINE = {
    "selection": "elite",
    "crossover": "one_point",
    "mutation": "gene",
    "triangles": 50,
    "survival": "additive",
}

EXPERIMENTS = {
    "selection": [
        {**BASELINE, "selection": "tournament_deterministic"},
        {**BASELINE, "selection": "roulette"},
        {**BASELINE, "selection": "ranking"},
    ],
    "crossover": [
        {**BASELINE, "crossover": "two_point"},
        {**BASELINE, "crossover": "uniform"},
    ],
    "triangles": [
        {**BASELINE, "triangles": 20},
        {**BASELINE, "triangles": 100},
    ],
}


def config_name(cfg: dict) -> str:
    return f"{cfg['selection']}_{cfg['crossover']}_{cfg['mutation']}_t{cfg['triangles']}"


def run_single(cfg: dict, seed: int) -> dict:
    out_dir = Path("results") / config_name(cfg) / f"seed_{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    result_file = out_dir / "triangles.json"
    if result_file.exists():
        print(f"  Skipping {config_name(cfg)} seed={seed} (already done)")
        with open(result_file) as f:
            data = json.load(f)
        return {
            "config": cfg,
            "seed": seed,
            "out_dir": str(out_dir),
            "elapsed": data.get("elapsed", 0),
            "final_fitness": data["final_fitness"],
            "final_error": data["final_error"],
            "fitness_history": data["fitness_history"],
            "error_history": data["error_history"],
        }

    cmd = [
        "uv", "run", "ga-triangles",
        "--image", IMAGE,
        "--triangles", str(cfg["triangles"]),
        "--generations", str(GENERATIONS),
        "--population-size", str(POPULATION),
        "--selection", cfg["selection"],
        "--crossover", cfg["crossover"],
        "--mutation", cfg["mutation"],
        "--survival", cfg.get("survival", "additive"),
        "--seed", str(seed),
        "--output-dir", str(out_dir),
    ]

    start = time.time()
    subprocess.run(cmd, check=True)
    elapsed = time.time() - start

    with open(result_file) as f:
        data = json.load(f)

    # Write elapsed time back into the JSON
    data["elapsed"] = elapsed
    with open(result_file, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return {
        "config": cfg,
        "seed": seed,
        "out_dir": str(out_dir),
        "elapsed": elapsed,
        "final_fitness": data["final_fitness"],
        "final_error": data["final_error"],
        "fitness_history": data["fitness_history"],
        "error_history": data["error_history"],
    }


def run_experiment(configs: list[dict]) -> dict[str, list]:
    results = {}
    all_configs = [BASELINE] + configs
    for cfg in all_configs:
        name = config_name(cfg)
        results[name] = []
        for seed in SEEDS:
            print(f"Running {name} seed={seed}...")
            r = run_single(cfg, seed)
            results[name].append(r)
    return results

def write_summary():
    """Scan all result directories and write a summary table."""
    rows = []
    for config_dir in sorted(RESULTS_DIR.iterdir()):
        if not config_dir.is_dir():
            continue
        for seed_dir in sorted(config_dir.iterdir()):
            result_file = seed_dir / "triangles.json"
            if not result_file.exists():
                continue
            with open(result_file) as f:
                data = json.load(f)
            rows.append({
                "config": config_dir.name,
                "seed": seed_dir.name,
                "final_fitness": round(data.get("final_fitness", 0), 6),
                "final_error": round(data.get("final_error", 0), 6),
                "n_generations": data.get("n_generations_run", "?"),
                "elapsed_s": round(data.get("elapsed", 0), 1),
                "approximation": str(seed_dir / "approximation.png"),
                "fitness_plot": str(seed_dir / "fitness.png"),
            })

    # Write markdown table
    if not rows:
        return
    headers = list(rows[0].keys())
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")

    summary_path = Path("results/summary.md")
    summary_path.write_text("\n".join(lines))
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    ''' 
    for exp_name, configs in EXPERIMENTS.items():
        print(f"\n=== Experiment: {exp_name} ===")
        #run_experiment(configs)
    '''
    run_experiment(EXPERIMENTS["selection"][:1]) #test
    print("\nAll experiments done. Run analyse.py to generate plots.")
    write_summary()