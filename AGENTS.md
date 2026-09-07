# AGENTS.md

This is a university group project for genetic algorithms. Optimize for the student's understanding and ability to defend the work, not for finishing code quickly.

## Working contract

- Read [CLAUDE.md](CLAUDE.md) for the full learning, debugging, and academic-integrity contract. Preserve it when assisting in this repository.
- Ask what the student has tried when the question is open-ended. Explain the concept before the implementation.
- For graded source logic, provide reasoning, pseudocode, signatures, or TODO skeletons rather than complete implementations. Do not edit source files unless the student explicitly asks for the edit or writes `TEACHING MODE OFF`.
- When debugging, first restate actual versus expected behavior, identify candidate causes, and propose one experiment that distinguishes them. Describe the fix only after the cause is established.
- During review, prioritize correctness, edge cases, complexity, validation, test assertions, and justification of design choices. Separate definite bugs from alternatives.
- Do not draft report or slide prose for submission. Critique and outline it instead.

## Project facts

- Python requirement: `>=3.11`; dependencies and the locked environment are managed with `uv`.
- Setup: `uv sync`.
- Tests: `uv run pytest tests/ -v` or `make test`.
- CLI smoke check: `uv run python -m ga_triangles.cli --help`.
- `make clean` uses Unix `find` syntax and may not work in PowerShell; use a Windows-compatible cleanup command when needed.
- Keep datasets in `data/` and generated outputs in `results/`; both are ignored. Notebooks are for exploration only and must not supply logic imported by `src/`.

## Architecture

The package pipeline is target loading (`image_io.py`), individual/genome representation (`individual.py`), rendering (`render.py`), fitness (`fitness.py`), parent selection (`selection.py`), crossover (`crossover.py`), mutation (`mutation.py`), survivor choice (`survival.py`), metrics (`metrics.py`), and orchestration/configuration (`engine.py`, `config.py`, `cli.py`). Strategy selection is dispatched through `GAConfig` and `engine.run_ga`.

The genome representation is a shared dependency: settle changes to `Individual`/`Triangle` before reasoning about selection, crossover, or mutation. `Triangle` is frozen; mutation should replace genes and invalidate cached fitness. Rendering uses Pygame and display helpers should remain separate from headless rendering tests.

## Selection and fitness guidance

- Treat selection methods as probability/distribution contracts: state the expected bias, normalization, replacement behavior, and handling of invalid or degenerate fitness values before coding.
- For roulette, universal, ranking, tournament, and Boltzmann selection, use tiny hand-checkable populations and assertions rather than relying on printed output.
- Avoid mutable default arguments, unchecked zero fitness totals, raw exponential overflow, and tests that open a Pygame window or only print results.
- Use the existing tests and [README.md](README.md) for project conventions. Preserve [docs/exercise1_ascii_art.md](docs/exercise1_ascii_art.md) and the assignment in `Task description/` as documentation references rather than copying them into this file.

## Change and validation discipline

Keep changes narrow and consistent with existing APIs. After an edit, run the smallest relevant pytest selection first, then the full suite when practical. Do not commit, push, or create branches on the student's behalf.
