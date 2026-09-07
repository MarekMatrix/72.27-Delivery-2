"""Guard against misleading aggregation and mixing experimental settings."""
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.analysis import Run, convergence_summary, group_runs, load_runs, summarize


def make_run(seed=42, history=(0.8, 0.4, 0.4), elapsed=None, **settings):
    config = dict(random_seed=seed, selection_method="elite", crossover_method="one_point",
                  mutation_method="gene", survival_strategy="additive", population_size=10,
                  n_triangles=50, n_generations=2, target_image_path="data/test.png")
    config.update(settings)
    return Run(Path(f"example/seed_{seed}/triangles.json"), config, history[-1],
               1 / (1 + history[-1]), np.array(history), len(history) - 1, elapsed, "maximum generations reached")


def test_all_seeds_and_initial_generation_are_used():
    runs = [make_run(history=(0.8, 0.4, 0.5)), make_run(seed=123, history=(0.6, 0.2))]
    generations, bands = convergence_summary(runs)
    np.testing.assert_array_equal(generations, [0, 1])
    np.testing.assert_allclose(bands, [[0.65, 0.25], [0.7, 0.3], [0.75, 0.35]])
    assert runs[0].generation_best == 1
    assert runs[0].error == 0.5  # returned solution is not replaced with best-so-far


def test_missing_runtime_and_single_run_are_not_zero():
    row = summarize([make_run()])
    assert row["median_runtime_s"] is None
    assert row["runtime_runs"] == 0
    assert row["std_mse"] is None
    assert row["iqr_mse"] is None


def test_statistics_and_threshold_failures():
    row = summarize([make_run(history=(0.8, 0.2), elapsed=2),
                     make_run(seed=123, history=(0.8, 0.6), elapsed=4)], threshold=0.3)
    assert row["median_mse"] == pytest.approx(0.4)
    assert row["std_mse"] == pytest.approx(np.sqrt(0.08))
    assert row["iqr_mse"] == pytest.approx(0.2)
    assert row["threshold_successes"] == 1
    assert row["median_generation_to_threshold"] == 1
    assert summarize([make_run()], threshold=0.1)["median_generation_to_threshold"] is None
    assert summarize([make_run()], threshold=0.9)["median_generation_to_threshold"] == 0


def test_only_one_factor_changes_and_population_is_detected():
    baseline = make_run()
    runs = [baseline, make_run(selection_method="ranking"),
            make_run(selection_method="ranking", population_size=100),
            make_run(population_size=100), make_run(target_image_path="other.png")]
    groups = group_runs(runs, baseline.config, "selection_method")
    assert set(groups) == {"elite", "ranking"}
    assert len(groups["ranking"]) == 1
    assert set(group_runs(runs, baseline.config, "population_size")) == {10, 100}


def save_run(directory, run):
    directory.mkdir(parents=True)
    (directory / "triangles.json").write_text(json.dumps({
        "config": run.config, "final_error": run.error, "final_fitness": run.fitness,
        "error_history": run.history.tolist(), "n_generations_run": run.generations,
    }))


def test_duplicate_seeds_cannot_inflate_sample_size(tmp_path):
    save_run(tmp_path / "one" / "seed_42", make_run())
    save_run(tmp_path / "copy" / "seed_42", make_run())
    with pytest.raises(ValueError, match="Duplicate config/seed"):
        load_runs(tmp_path)


def test_bad_history_is_reported(tmp_path):
    save_run(tmp_path / "one" / "seed_42", make_run())
    path = tmp_path / "one" / "seed_42" / "triangles.json"
    data = json.loads(path.read_text())
    data["n_generations_run"] = 99
    path.write_text(json.dumps(data))
    runs, warnings = load_runs(tmp_path)
    assert not runs
    assert "history must include generation 0" in warnings[0]
