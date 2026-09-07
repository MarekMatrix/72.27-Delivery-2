# Experiment execution and analysis

The runner now separates campaigns, checks cached settings and supports population
size as an experimental factor. No main experiment campaign has been run yet.
The defaults remain a smoke test: **population 10, 5 generations, seeds 42/123**.
Choose the main budget after a pilot.

## Inspect the plan first

```bash
uv run python experiments/experiments.py --dry-run --experiment all \
  --results-dir results/full_campaign \
  --population-size 100 --generations 200 \
  --population-sizes 50 100 200 \
  --seeds 42 123 456 789 1337 2024 2025 31415 27182 8675309
```

This example prints **10 distinct configurations × 10 seeds = 100 runs** and
writes nothing. The population and generation values are a pilot proposal, not a
validated final budget. Remove `--dry-run` only when ready to run the selected plan.

`--experiment` accepts `baseline` (default), `selection`, `crossover`, `triangles`,
`population`, or `all`. Every group includes the same baseline; duplicate baseline
settings are run once and verified cached results are reused across groups.
`--population-size` sets the baseline and all non-population comparisons;
`--population-sizes` supplies the population alternatives. Use even population
sizes because the engine pairs parents. Seeds must be distinct and non-negative.

A baseline-only pilot could be launched separately with:

```bash
uv run python experiments/experiments.py --experiment baseline \
  --results-dir results/pilot \
  --population-size 100 --generations 200 --seeds 42 123 456
```

The default result directory is `results/full_campaign`, separate from existing
legacy results in `results/`. Use a different `--results-dir` for each changed
campaign setup. Relative output paths are relative to your working directory;
relative image paths resolve against the repository root.

## Stored settings and safe reuse

`campaign.json` stores the effective baseline, its directory name, the seed list,
the target's SHA-256, and all four planned experiment groups. After the campaign
starts, changing its baseline, budget, seeds, target bytes or group definitions
requires a new campaign directory. Selecting another experiment group with the
same settings is allowed.

Each configuration directory includes selection, crossover, mutation, triangle
count, population size, generation budget and a short SHA-256 of **all effective
GA settings plus target bytes**. Seed is a separate subdirectory:

```
results/full_campaign/
  campaign.json
  <configuration>/seed_42/
    triangles.json
    approximation.png
    fitness.png
  summary.md
```

Before skipping a completed run, the runner checks the entire saved configuration
against the requested configuration (including CLI defaults and seed), target hash,
completed budget, histories, final metrics, both timings and expected output files.
Mismatched or incomplete records produce an error instead of silently being reused
or overwritten. Baseline comparison and cached settings share the CLI's configuration
builder so default values do not drift between the runner and CLI.

The runner is intended for sequential use. Run it in the project's environment;
it launches child runs with the same Python interpreter. Finish one runner before
starting another in the same campaign directory. Code revision and machine identity
are not part of the cache identity: use a new campaign after implementation changes
or when collecting measurements on different hardware, and record that context.

## Two timing measurements

- `ga_elapsed_s`: `time.perf_counter()` immediately around `run_ga(...)` in the
  CLI. Includes initialization, evolution and in-loop metric evaluation. Excludes
  loading the target and exporting the final image/plot/JSON.
- `elapsed`: the runner's monotonic wall-clock measurement of the entire child
  process, including Python startup, target loading and output generation. It
  excludes the runner's own target hashing and metadata/summary writes.

Both values are seconds. The analysis keeps them separate: runtime figures and
speed leaders use **GA time**; total time remains visible in tables/CSV. Old runs
without `ga_elapsed_s` have missing GA timing, never a zero or a total-time fallback.
No per-generation timestamps are collected, so seconds to a quality threshold
cannot be reconstructed from these totals.

## Results and analysis

```bash
uv run python experiments/analysis.py --results-dir results/full_campaign
```

Baseline and expected seed count are read from `campaign.json`. Override with
`--baseline <directory-name>` or `--expected-runs <n>` only when needed.
Legacy results remain readable with `uv run python experiments/analysis.py`;
without a manifest the original baseline and expected count of 10 are used.

Open `<results-dir>/analysis/analysis.md` for sections **4.1–4.6**. Exports include
PNG/PDF figures, `runs.csv` (saved config and both timings),
`configuration_summary.csv` (per experiment), and `overall_summary.csv`
(each configuration once). Generated files stay gitignored.

For interactive reading and discussion, open `notebooks/analysis.ipynb`, set
`RESULTS_DIR`, and run all cells. Leave `BASELINE` and `EXPECTED_RUNS` as `None`
to use campaign metadata. The notebook imports the same analysis functions.
Use the project's environment as the kernel. If necessary, install the optional
development dependency with `uv add --dev ipykernel`, then select `.venv` in your
notebook editor. The standalone script needs no notebook dependencies.

The assignment (`Task description/SIA - TP2 - 2026 2Q.pdf`, pp. 2–4) asks for
fitness/error/generation metrics and justification of the algorithm. Ten runs and
the section order are the proposed analysis design, not assignment requirements.
This analysis concerns Exercise 2; Exercise 1 is design-only.

## Reading the results

- **Quality:** final normalized MSE (0–1, lower is better), median and mean.
- **Speed:** median GA time and best-so-far MSE per generation. Generation 0 is
  initialization. Early generation-of-best can indicate stagnation at poor quality.
- **Stability:** final-MSE boxplots with all runs, sample SD and IQR. Shaded
  convergence bands show the middle 50% of observations, not confidence intervals.
  SD/IQR are unavailable for one run.

All comparisons change one saved setting from the same baseline. Missing planned
configurations and repetition counts are flagged. Different-length histories are
plotted only through the shortest run in each comparison. Duplicate config/seed
records fail rather than inflate the number of independent observations.

The triangle panel displays the run nearest median final MSE and the current
target file. Inspect visual differences yourself; pixel error alone does not
establish perceptual quality. Legacy results lack a target hash.

Optionally choose a shared quality target **before** comparing outcomes:

```bash
uv run python experiments/analysis.py --results-dir results/full_campaign --mse-threshold 0.10
```

`0.10` is only an example. The extra table reports successes/all runs and median
first-hit generation among successes. Unsuccessful runs remain in the denominator.

Use consistent hardware and execution conditions. Equal generation budgets are
not equal compute budgets across populations or triangle counts. Overall leaders
are descriptive; combining preferred settings from separate experiments requires
a new validation experiment.
