# Experiment execution and analysis

The runner now separates campaigns, checks cached settings and supports population
size and survival strategy as experimental factors. No main experiment campaign has been run yet.
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

This example prints **17 distinct configurations × 10 seeds = 170 runs** and
writes nothing. The population and generation values are a pilot proposal, not a
validated final budget. Remove `--dry-run` only when ready to run the selected plan.

`--experiment` accepts `baseline` (default), `selection`, `crossover`, `triangles`,
`population`, `survival`, `mutation`, or `all`. Every group includes the same baseline; duplicate baseline
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
the target's SHA-256, and all six planned experiment groups. After the campaign
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
It also requires the exported triangle geometry and canvas metadata. Older JSON
files without these remain readable by the analysis, but cannot be reused as
complete outputs for a new campaign. Existing results are not modified.
Mismatched or incomplete records produce an error instead of silently being reused
or overwritten. Baseline comparison and cached settings share the CLI's configuration
builder so default values do not drift between the runner and CLI.

The runner is intended for sequential use. Run it in the project's environment;
it launches child runs with the same Python interpreter. Finish one runner before
starting another in the same campaign directory. Code revision and machine identity
are not part of the cache identity: use a new campaign after implementation changes
or when collecting measurements on different hardware, and record that context.

`triangles.json` stores the returned individual's triangles in drawing order,
with `vertices` (three normalized x/y pairs) and `color` (normalized RGBA).
Coordinates and colour components are numeric values in [0, 1]. `canvas` stores
width, height and `background_rgb` in [0, 255], allowing the saved solution to be
rendered without the target image. GA timing excludes this final export.

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

Open `<results-dir>/analysis/analysis.md` for sections **4.1–4.8**. Exports include
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
  initialization. Survival curves instead use current-generation best MSE to show losses.
  Early generation-of-best can indicate stagnation at poor quality.
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


## Figure titles and how to read them

Each exported figure includes the report section and experiment name, a question,
the target and fixed settings, descriptive axis labels, and a reading guide.
The file names also identify the section, for example
`4_2_selection_convergence.png` and `4_5_population_ga_runtime.png`.

Section 4.1 first shows the baseline seeds individually, with a per-run table and
all their generated images. These lines are repetitions of the **same configuration**.
A baseline-only pilot does not yet compare different selection methods or other
parameter values. Sections 4.2–4.7 omit comparison figures until at least two
values of their factor are available; section 4.8 does not rank a lone baseline.

Once alternative configurations exist:

- **Convergence:** each colour is a configuration, the line is its median
  best-so-far MSE, and shading is the middle 50% of its runs. Read lower curves as
  better quality at that generation; this is not elapsed-time convergence.
- **Survival convergence (4.6):** median current-generation best MSE with IQR.
  Increases show lost quality; median curves can hide losses in individual seeds.
  This is deliberately not a cumulative best-so-far curve.
- **Final MSE:** each dot is a run, the box spans the middle 50%, and the line
  inside is the median. Lower boxes mean better quality; shorter boxes mean less
  variation. Whiskers extend to observations within 1.5 × IQR. All runs, including
  outliers, are visible as dots.
- **GA runtime:** the same distribution view in seconds; lower is faster.
- **Images:** compare recognizable shapes and colours, as well as numeric MSE.
  The triangle-count comparison uses the run nearest each configuration's median.

A main experiment budget is the chosen generation limit and repetitions for the
final comparisons. For example, 200 generations and 10 seeds across 17 distinct
configurations require 170 runs. It is not a guarantee of convergence or a fixed
wall-clock limit. Pilot runs help decide whether that workload and progress are
appropriate before collecting the full results.

For the current flag pilot:

```bash
uv run python experiments/analysis.py --results-dir results/pilot_argentina
```

Open `results/pilot_argentina/analysis/analysis.md` for the updated figures and
captions. Regenerating the analysis does not launch any GA runs. Older exported
figures may remain in previously used output directories; `analysis.md` links to
the figures generated by the current script.

## Preview every figure before running the full campaign

```bash
uv run python experiments/preview_figures.py
```

This creates `results/figure_preview/preview.md`, a local `index.html` gallery,
and `all_figures_preview.pdf` with all 16 figures. It uses the same plotting
functions as the real analysis, with 10 synthetic seeds for each configuration.
Sections 4.2–4.7 therefore show all planned alternatives. Section 4.8 previews
the summary table in Markdown; it does not add another chart.

Every figure is marked **SYNTHETIC PREVIEW — NOT EXPERIMENT RESULTS**. Curves,
errors and runtimes are illustrative. Existing pilot images are reused unchanged
as placeholders, and do not correspond to the synthetic configurations or MSE
labels. No GA is run and no synthetic run JSON is written. The actual pilot
results remain separate. Use this preview only to review layout and readability.

The preview defaults to the Argentina pilot for image placeholders. Override
with `--pilot-dir <campaign>` and `--output-dir <preview-folder>` if needed.

## Survival comparison (4.6)

`--experiment survival` compares additive and exclusive with identical baseline
settings, generation budget and seeds. The runner includes the baseline once and
reuses validated results from the same campaign, so this adds 10 exclusive runs
to a completed additive baseline with 10 seeds. `--experiment all` includes it.

Use the same arguments as the full plan above, replacing `--experiment all` with
`--experiment survival`. Keep `--dry-run` to inspect the plan without running GA.
Choose `--image "data/FlagArgentina – lite.png"` for the Argentina target; the
runner default is still `data/skrik.png`.

The report shows current-generation best MSE convergence, a final-MSE boxplot
with individual seeds, and a table including median GA runtime and MSE spread.
Overall comparison is now section 4.8. Both survival methods are required
implementations in the assignment; this comparison is our analysis design.

Older campaign manifests contain fewer groups or selection alternatives. They remain
readable by the analysis, but the runner rejects extending them with this changed
plan. Use a new campaign directory for the expanded plan; existing pilot files
are left intact. Baseline reuse applies within the new campaign.

## Complete method comparisons

Selection (4.2) includes all seven implemented methods: elite, roulette, universal,
Boltzmann, deterministic tournament, probabilistic tournament and ranking.
Tournament settings and Boltzmann temperature use the saved configuration defaults;
these experiments do not tune each method separately.

Mutation (4.7) includes gene, multigene, uniform and complete. Run it with
`--experiment mutation`, using the same image, budget, seeds and result directory
as the other groups in the new campaign. It is also included in `--experiment all`.
The additive baseline with gene mutation is reused, leaving three extra mutation
configurations. Every comparison changes only its named factor.

Mutation figures show median best-so-far MSE with IQR and final-MSE boxplots with
individual seeds. The accompanying table includes MSE spread and GA runtime.
The numerical mutation rate stays fixed, but its meaning differs between methods:
gene can perturb one triangle per individual, multigene tests a random subset,
uniform tests each triangle, and complete perturbs all triangles when triggered.
Each selected triangle has one coordinate or colour component changed. This
compares the implemented operators at a common rate, not equal mutation counts.

With baseline population 100 and triangle count 50, the full plan has 17 distinct
configurations: baseline + 6 selection + 2 crossover + 2 triangle counts +
2 population sizes + 1 survival + 3 mutation. Ten seeds give 170 runs, not a
Cartesian product of all settings. Defaults remain a small smoke test; inspecting
the plan or generating figures never starts the full campaign.
