# Contributing

Thank you for considering a contribution.

## Before starting

- Read `AGENTS.md` and relevant project documentation.
- Search existing issues and pull requests for related work.
- For substantial changes, discuss the proposed approach before implementation.
- Do not include unrelated refactoring or formatting churn.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Changes

- Keep changes focused and reviewable.
- Preserve existing behavior unless a change is intentional and documented.
- Add or update tests for behavior changes.
- Update documentation when interfaces, behavior, configuration, or workflows change.
- Follow the versioning and changelog policy.
- Never commit secrets, local configuration, virtual environments, or generated artifacts.

## Validation

Run relevant checks before opening a pull request:

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

Report checks that could not be run. Do not claim unrun checks passed.

## Pull requests

Explain what changed and why, important implementation decisions, tests/checks performed, documentation/version/changelog updates, compatibility or migration implications, and known limitations. Keep each pull request focused on one coherent change.
