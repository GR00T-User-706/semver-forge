# Development Guide

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Common checks

```bash
ruff check .
ruff format --check .
pytest
python -m compileall src
python -m build
```

## Working rules

- Read `AGENTS.md` before making changes.
- Keep changes focused.
- Add tests for behavior changes.
- Update documentation when behavior or workflows change.
- Follow `docs/VERSIONING.md` and update `CHANGELOG.md` for meaningful changes.
- Do not commit local environments, secrets, caches, or build outputs.

## Adding dependencies

Add runtime dependencies to `project.dependencies` and development tools to an optional group. Document non-obvious dependencies and verify compatibility with the declared Python range.
