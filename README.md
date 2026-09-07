# TP2 — Algoritmos Genéticos: Aproximación de imágenes con triángulos

SIA (72.27), ITBA. See `Task description/SIA - TP2 - 2026 2Q.pdf` for the full assignment.

Ejercicio 2: evolve a population of individuals, each a fixed-size list of
translucent triangles, so that rendering them on a blank canvas approximates
a target image. No external library may be used for the GA itself (selection,
crossover, mutation, survival) — only for image I/O.

Ejercicio 1 (ASCII art via GA) is design-only, see `docs/exercise1_ascii_art.md`.

## Setup

Dependencies and the virtual environment are managed with
[uv](https://docs.astral.sh/uv/). Install uv once (see their docs), then:

```bash
uv sync
```

This creates `.venv/` and installs everything pinned in `uv.lock` (committed,
so everyone resolves the exact same versions). Add a new dependency with
`uv add <package>`, or a dev-only one with `uv add --dev <package>` — either
updates `pyproject.toml` and `uv.lock` together, don't edit them by hand.

## Running

```bash
uv run ga-triangles --image data/flag.png --triangles 100 --generations 500 \
    --selection tournament_deterministic --crossover uniform --mutation multigene \
    --survival additive
```

Run `uv run ga-triangles --help` to see this listing from the tool itself.
Outputs land in `results/`: the approximated image, a fitness-over-generations
plot, and a JSON dump of the run config + stop reason.

### Flags

| Flag | Type | Default | Meaning |
|---|---|---|---|
| `--image` | path | first image file found in `data/` | Target image to approximate. |
| `--triangles` | int | *required* | Number of triangles per individual (genome size). |
| `--output-dir` | path | `results` | Directory for the approximation image, fitness plot, and config/result JSON. |
| `--population-size` | int | `100` | Number of individuals per generation. |
| `--generations` | int | `500` | Number of generations to run. |
| `--min-error` | float | none | Optional early-stop threshold on `pixel_error`; stops once reached, even if `--generations` hasn't. |
| `--selection` | choice | `elite` | `elite`, `roulette`, `universal`, `boltzmann`, `tournament_deterministic`, `tournament_probabilistic`, `ranking`. |
| `--crossover` | choice | `one_point` | `one_point`, `two_point`, `uniform`, `ring`. |
| `--mutation` | choice | `gene` | `gene`, `multigene`, `uniform`, `non_uniform`. |
| `--survival` | choice | `additive` | `additive` ((μ+λ): parents and offspring compete) or `exclusive` ((μ,λ): only offspring survive). |
| `--crossover-rate` | float | `0.9` | Probability that a selected pair actually crosses over (vs. being copied through). |
| `--mutation-rate` | float | `0.05` | Per-gene (or per-individual, depending on the method) mutation probability. |
| `--seed` | int | none | Random seed, for reproducible runs. |

Note: `GAConfig` (`src/ga_triangles/config.py`) also defines `tournament_size`,
`tournament_probability`, and `boltzmann_temperature`, but `cli.py` doesn't
currently expose them as flags — tournament and Boltzmann selection always run
with their hardcoded defaults (size 3, probability 0.75, temperature 1.0)
until someone adds the corresponding flags.

## Pipeline

```
target image ──► load & resize (image_io.py)
                        │
                        ▼
        random initial population (individual.py)
                        │
        ┌───────────────▼────────────────┐
        │   generation loop (engine.py)   │
        │                                  │
        │  render each individual ────────┼─► render.py
        │  score vs. target ───────────────┼─► fitness.py
        │  select parents ──────────────────┼─► selection.py
        │  crossover + mutate ───────────────┼─► crossover.py, mutation.py
        │  form next generation ─────────────┼─► survival.py
        │  log best/mean fitness, error ─────┼─► metrics.py
        │                                  │
        └───────────────┬────────────────┘
                         │ stop condition met
                         ▼
        best individual → final image + triangle list + plots
```

Every pluggable stage (selection / crossover / mutation / survival method) is
chosen via `GAConfig` (`src/ga_triangles/config.py`) and dispatched by
`engine.run_ga`, so different strategies can be compared without touching the
loop itself.

## Module map & suggested task split (6 people)

Each module currently only has function signatures, docstrings and `# TODO`s —
no logic. Pick one area, fill it in, write its tests, and write the
corresponding section of the report justifying the design decisions.

| Area | Files | Involves |
|---|---|---|
| **1. Image I/O & rendering** | `image_io.py`, `render.py` | Load/resize target image (Done, Marek); rasterize a list of translucent triangles onto a canvas with alpha blending. Pillow/numpy allowed here. |
| **2. Representation & fitness** | `individual.py`, `fitness.py` | Decide the genome encoding (flat array vs. object list) — this choice affects everyone else. Define the error metric and fitness function; **write down the justification**, the TP asks for it explicitly. |
| **3. Selection** | `selection.py` | All 7 required methods: Elite, Ruleta, Universal, Boltzmann, Torneo (deterministic + probabilistic), Ranking. |
| **4. Crossover** | `crossover.py` | At least 2 of the 4 methods (one-point, two-point, uniform, ring). Decide (and justify) when each is appropriate. |
| **5. Mutation** | `mutation.py` | At least 2 of the 4 methods (gene, multigene, uniform, non-uniform). Decide (and justify) when each is appropriate. |
| **6. Engine, survival & experiments** | `engine.py`, `survival.py`, `metrics.py`, `cli.py`, `config.py` | Both survival strategies (additive/exclusive), stopping criteria, the main loop wiring everything together, and running the actual experiments/report figures once the pieces above exist. Natural to finish last since it depends on 1–5. |

Crossover and mutation were split into separate areas (4 and 5) rather than
one person owning both, since the TP treats them as two independent
requirements (each needs ≥2 implemented methods and its own justification)
and they don't share code beyond the `Individual` type.

Area 2's decision (genome encoding) should be settled and communicated to the
group *before* 3, 4 and 5 start, since selection/crossover/mutation all
operate on that structure. Everything else can proceed in parallel against
the function signatures already in place — mock a fake `Individual`/fitness
if you need to unblock before area 2 lands.

Before running real experiments, answer the "Preguntas que deben realizarse
ANTES de experimentar" from the TP statement (see PDF, page 4) as a group —
they're a good comprehension check regardless of who owns which module.

## Structure

```
src/ga_triangles/  # the package — everything importable
tests/             # one test file per module above
notebooks/         # exploration only, nothing here is a deliverable
data/              # input images (gitignored, don't commit datasets)
results/           # generated outputs (gitignored, don't commit)
docs/              # report + presentation source
Task description/  # assignment PDF
```
