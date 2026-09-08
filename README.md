# TP2 — Algoritmos Genéticos: Aproximación de imágenes con triángulos

Evolve a population of individuals, each a fixed-size list of
translucent triangles, so that rendering them on a blank canvas approximates
a target image.

## Setup
Python requirement: `>=3.11`
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

Run `uv run ga-triangles --help` for every flag (population size, rates, seed, etc).
Outputs land in `results/`: the approximated image, a fitness-over-generations
plot, and `triangles.json` containing the run configuration, metrics, canvas
dimensions/background, and the returned individual's triangles in drawing order.
Each triangle has three normalized `(x, y)` vertices and a normalized RGBA `color`
(all values in `[0, 1]`). Later triangles are drawn over earlier ones. The canvas
background uses RGB integers in `[0, 255]`.

## Pipeline

```
target image ──► load & resize (image_io.py)
                        │
                        ▼
        random initial population (individual.py)
                        │
        ┌───────────────▼────────────────┐
        │   generation loop (engine.py)  │
        │                                │
        │  render each individual ───────┼─► render.py
        │  score vs. target ─────────────┼─► fitness.py
        │  select parents ───────────────┼─► selection.py
        │  crossover + mutate ───────────┼─► crossover.py, mutation.py
        │  form next generation ─────────┼─► survival.py
        │  log best/mean fitness, error ─┼─► metrics.py
        │                                │
        └───────────────┬────────────────┘
                        │ stop condition met
                        ▼
        best individual → final image + triangle list + plots
```

Every pluggable stage (selection / crossover / mutation / survival method) is
chosen via `GAConfig` (`src/ga_triangles/config.py`) and dispatched by
`engine.run_ga`, so different strategies can be compared without touching the
loop itself.

## Module map

| **1. Image I/O & rendering** | `image_io.py`, `render.py` | Load/resize target image; rasterize a list of translucent triangles onto a canvas with alpha blending. |
| **2. Representation & fitness** | `individual.py`, `fitness.py` | Decide the genome encoding (object list). Define the error metric and fitness function; 
| **3. Selection** | `selection.py` | Methods: Elite, Ruleta, Universal, Boltzmann, Torneo (deterministic + probabilistic), Ranking. |
| **4. Crossover** | `crossover.py` | Methods: one-point, two-point, uniform. |
| **5. Mutation** | `mutation.py` | Methods: gene, multigene, uniform. |
| **6. Engine, survival & experiments** | `engine.py`, `survival.py`, `metrics.py`, `cli.py`, `config.py` | Both survival strategies (additive/exclusive), stopping criteria, the main loop wiring everything together, and running the actual experiments figures once the pieces above exist. |


## Structure

```
src/ga_triangles/  # the package — everything importable
data/              # input images (gitignored, don't commit datasets)
results/           # generated outputs (gitignored, don't commit)
```
