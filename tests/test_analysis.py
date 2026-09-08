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


def test_survival_plot_preserves_losses_and_excludes_other_changes(tmp_path, monkeypatch):
    from experiments import analysis
    baseline = make_run(history=(0.8, 0.4, 0.3))
    exclusive = make_run(history=(0.8, 0.3, 0.5), survival_strategy="exclusive")
    groups = group_runs([baseline, exclusive,
                        make_run(survival_strategy="exclusive", population_size=100)],
                       baseline.config, "survival_strategy")
    assert groups == {"additive": [baseline], "exclusive": [exclusive]}
    def inspect_figure(fig, *args, **kwargs):
        ax = fig.axes[0]
        np.testing.assert_allclose(ax.lines[1].get_ydata(), [0.8, 0.3, 0.5])
        assert "Current-generation" in ax.get_ylabel()
        assert kwargs["title"].startswith("4.6 Survival")
        analysis.plt.close(fig)
        return "checked"
    monkeypatch.setattr(analysis, "save_figure", inspect_figure)
    analysis.plot_convergence(groups, tmp_path, "survival", "survival")
    _, bands = convergence_summary([exclusive])
    np.testing.assert_allclose(bands[1], [0.8, 0.3, 0.3])
    assert summarize([exclusive])["median_mse"] == 0.5


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


def test_mutation_report_exports_all_methods_and_excludes_changed_rates(tmp_path):
    import csv
    from experiments.analysis import build_analysis
    for method in ("gene", "multigene", "uniform", "complete"):
        save_run(tmp_path / method / "seed_42", make_run(mutation_method=method, mutation_rate=0.05))
    save_run(tmp_path / "different_rate" / "seed_42",
             make_run(mutation_method="uniform", mutation_rate=0.2))
    report = build_analysis(tmp_path, baseline_name="gene", expected_runs=1)
    content = report.read_text()
    assert "## 4.7 Mutation methods" in content
    assert "## 4.8 Overall comparison" in content
    assert "Excluded" in content and "different_rate" in content
    assert "same numerical mutation rate does not imply" in content
    for name in ("4_7_mutation_convergence", "4_7_mutation_final_mse"):
        assert (report.parent / f"{name}.png").exists()
    with (report.parent / "configuration_summary.csv").open() as stream:
        rows = [row for row in csv.DictReader(stream) if row["experiment"] == "mutation"]
    assert {row["configuration"] for row in rows} == {"gene", "multigene", "uniform", "complete"}
    with (report.parent / "overall_summary.csv").open() as stream:
        assert len(list(csv.DictReader(stream))) == 4
