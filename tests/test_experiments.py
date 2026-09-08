"""Protect campaign identity, cache reuse and the scope of GA timing."""
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest

from experiments import experiments as runner
from experiments.analysis import build_analysis, load_runs, summarize
from ga_triangles import cli
from ga_triangles.individual import Individual, Triangle
from ga_triangles.render import render


def target_image(tmp_path):
    path = tmp_path / "target.png"
    Image.new("RGB", (8, 8), (80, 100, 120)).save(path)
    return path


def test_names_cover_all_settings_but_not_seed():
    cfg = runner.saved_config(runner.BASELINE, 42, "image.png", 5)
    name = runner.config_name(cfg, "image-hash")
    assert runner.config_name({**cfg, "random_seed": 123}, "image-hash") == name
    for field, value in [("population_size", 100), ("n_generations", 200),
                         ("mutation_rate", 0.2), ("crossover_rate", 0.1),
                         ("survival_strategy", "exclusive"), ("target_image_path", "other.png")]:
        assert runner.config_name({**cfg, field: value}, "image-hash") != name
    assert runner.config_name(cfg, "different-image-bytes") != name


def test_population_changes_one_factor():
    baseline = {**runner.BASELINE, "population_size": 100}
    plan = runner.experiment_plan(baseline, [50, 200])
    for cfg in plan["population"]:
        assert cfg["population_size"] in (50, 200)
        assert {k: v for k, v in cfg.items() if k != "population_size"} == {
            k: v for k, v in baseline.items() if k != "population_size"}


def test_dry_run_writes_nothing_and_deduplicates_baseline(tmp_path, monkeypatch, capsys):
    image = target_image(tmp_path)
    output = tmp_path / "campaign"
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **kw: pytest.fail("GA started"))
    runner.main(["--image", str(image), "--results-dir", str(output), "--dry-run",
                 "--experiment", "all", "--population-size", "100", "--seeds", "42", "123"])
    assert not output.exists()
    assert "17 configurations × 2 seeds = 34 runs" in capsys.readouterr().out


@pytest.mark.parametrize("factor,methods", [
    ("selection", {"elite", "roulette", "universal", "boltzmann", "ranking",
                   "tournament_deterministic", "tournament_probabilistic"}),
    ("mutation", {"gene", "multigene", "uniform", "complete"}),
])
def test_all_methods_run_with_identical_other_settings(tmp_path, monkeypatch, factor, methods):
    calls = []
    monkeypatch.setattr(runner, "run_single", lambda cfg, seed, **kw: calls.append((cfg, seed)))
    image = target_image(tmp_path)
    runner.main(["--image", str(image), "--results-dir", str(tmp_path / "campaign"),
                 "--experiment", factor, "--population-size", "100", "--seeds", "42", "123"])
    assert len(calls) == len(methods) * 2
    assert {(cfg[factor], seed) for cfg, seed in calls} == {
        (method, seed) for method in methods for seed in (42, 123)}
    baseline = {**runner.BASELINE, "population_size": 100}
    for cfg, _ in calls:
        assert {**cfg, factor: baseline[factor]} == baseline


def test_survival_changes_only_strategy_and_reuses_baseline(tmp_path, monkeypatch):
    baseline = {**runner.BASELINE, "population_size": 100}
    plan = runner.experiment_plan(baseline)["survival"]
    assert {cfg["survival"] for cfg in plan} == {"additive", "exclusive"}
    for cfg in plan:
        assert {**cfg, "survival": baseline["survival"]} == baseline
    calls = []
    monkeypatch.setattr(runner, "run_single", lambda cfg, seed, **kw: calls.append((cfg, seed)))
    image = target_image(tmp_path)
    runner.main(["--image", str(image), "--results-dir", str(tmp_path / "campaign"),
                 "--experiment", "survival", "--population-size", "100", "--seeds", "42", "123"])
    assert [(cfg["survival"], seed) for cfg, seed in calls] == [
        ("additive", 42), ("additive", 123), ("exclusive", 42), ("exclusive", 123)]


def test_campaign_rejects_changed_budget(tmp_path, monkeypatch):
    image = target_image(tmp_path)
    output = tmp_path / "campaign"
    monkeypatch.setattr(runner, "run_single", lambda *a, **kw: {})
    args = ["--image", str(image), "--results-dir", str(output)]
    runner.main(args)
    original = (output / "campaign.json").read_bytes()
    with pytest.raises(SystemExit):
        runner.main([*args, "--generations", "200"])
    assert (output / "campaign.json").read_bytes() == original


def test_cli_times_only_ga(tmp_path, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(cli.time, "perf_counter", lambda: clock[0])
    def load(path):
        clock[0] += 7  # image loading is outside the GA interval
        return np.zeros((8, 8, 3), dtype=np.uint8)
    def ga(target, config):
        clock[0] += 3
        return SimpleNamespace(best_individual=SimpleNamespace(fitness=0.8, triangles=[]),
                               history=SimpleNamespace(best_error=[0.25], best_fitness=[0.8],
                                                       plot=lambda path: None),
                               n_generations_run=0, stop_reason="maximum generations reached")
    def render(*args):
        clock[0] += 11  # final rendering is outside the GA interval
        return np.zeros((8, 8, 3), dtype=np.uint8)
    monkeypatch.setattr(cli, "load_target_image", load)
    monkeypatch.setattr(cli, "run_ga", ga)
    monkeypatch.setattr(cli, "render", render)
    cli.main(["--image", "unused.png", "--triangles", "2", "--output-dir", str(tmp_path)])
    assert json.loads((tmp_path / "triangles.json").read_text())["ga_elapsed_s"] == 3


@pytest.mark.parametrize("survival", ["additive", "exclusive"])
def test_real_run_resume_analysis_and_stale_config(tmp_path, monkeypatch, survival):
    image = target_image(tmp_path)
    output = tmp_path / "campaign"
    cfg = {**runner.BASELINE, "triangles": 2, "population_size": 2, "survival": survival}
    data = runner.run_single(cfg, 42, results_dir=output, image=str(image), generations=1)
    assert 0 < data["ga_elapsed_s"] < data["elapsed"]
    assert data["config"]["population_size"] == 2
    result_path = next(output.glob("*/seed_*/triangles.json"))
    # Exported geometry alone must reproduce the returned image, without the target.
    restored = Individual([
        Triangle(tuple(tuple(point) for point in triangle["vertices"]), tuple(triangle["color"]))
        for triangle in data["triangles"]
    ])
    canvas = data["canvas"]
    assert len(restored.triangles) == cfg["triangles"]
    reconstructed = render(restored, canvas["width"], canvas["height"], tuple(canvas["background_rgb"]))
    with Image.open(result_path.parent / "approximation.png") as saved_image:
        np.testing.assert_array_equal(reconstructed, np.asarray(saved_image))
    missing_geometry = {k: v for k, v in data.items() if k != "triangles"}
    with pytest.raises(ValueError, match="triangles"):
        runner.validate_result(missing_geometry, data["config"], result_path)
    original = result_path.read_bytes()
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **kw: pytest.fail("Cached GA restarted"))
    assert runner.run_single(cfg, 42, results_dir=output, image=str(image), generations=1) == data
    assert result_path.read_bytes() == original
    runs, warnings = load_runs(output)
    assert not warnings
    mixed = summarize([runs[0], replace(runs[0], ga_elapsed_s=None)])
    assert mixed["ga_runtime_runs"] == 1 and mixed["runtime_runs"] == 2
    assert mixed["median_ga_runtime_s"] == data["ga_elapsed_s"]
    runner.write_json(output / "campaign.json", {"baseline": result_path.parent.parent.name,
                                                "seeds": [42], "experiments": {}})
    report = build_analysis(output)
    assert "Planned runs/configuration: **1**" in report.read_text()
    assert "Speed: lowest median GA runtime" in report.read_text()
    data["config"]["n_generations"] = 200
    result_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Saved settings differ"):
        runner.run_single(cfg, 42, results_dir=output, image=str(image), generations=1)
    assert json.loads(result_path.read_text())["config"]["n_generations"] == 200


def test_missing_ga_timing_cannot_be_reused(tmp_path):
    expected = runner.saved_config(runner.BASELINE, 42, "image.png", 1)
    data = {"config": expected, "n_generations_run": 1, "error_history": [0.5, 0.25],
            "fitness_history": [2/3, 0.8], "final_error": 0.25, "final_fitness": 0.8}
    with pytest.raises(ValueError, match="ga_elapsed_s"):
        runner.validate_result(data, expected, tmp_path / "triangles.json")
