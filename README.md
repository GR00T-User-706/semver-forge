# Python Project Template

A reusable starting point for Python libraries, command-line tools, and applications.

This repository is a GitHub template. Create a new repository from it, then replace the project placeholders and remove optional components that do not apply.

## Quick start

1. Create a repository from this template.
2. Replace `package_name` with the import package name (valid Python identifier).
3. Update project metadata in `pyproject.toml`.
4. Set the initial version consistently in `pyproject.toml`, `src/package_name/__init__.py`, and `CHANGELOG.md`.
5. Replace this README with the project's purpose, installation, usage, and support information.
6. Review `AGENTS.md`, `docs/VERSIONING.md`, and `docs/BUILDING.md`.
7. Add runtime dependencies only when the project actually requires them.

## Layout

```text
src/package_name/   Importable Python package
tests/              Automated tests
docs/               Development, architecture, QA, and release docs
examples/           Runnable usage examples
packaging/          Distribution notes and release payload policy
.github/            CI, issue/PR templates, and review prompts
```

The `src/` layout prevents tests and repository-root files from accidentally satisfying imports that should resolve from an installed package.

## Development

Requires Python 3.10 or newer by default. Change the supported range in `pyproject.toml` to match the actual project.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

Windows activation: `.venv\\Scripts\\activate`.

## Build distributions

```bash
python -m pip install build
python -m build
python -m pip install --force-reinstall dist/*.whl
```

The resulting `dist/` directory contains the source distribution and wheel. Inspect and test both before publishing.

## Project standards

- Semantic Versioning: `docs/VERSIONING.md`
- Release workflow: `docs/RELEASE_PROCESS.md`
- Build instructions: `docs/BUILDING.md`
- QA checklist: `docs/QA_CHECKLIST.md`
- Security reporting: `SECURITY.md`
- Contribution process: `CONTRIBUTING.md`

## Template placeholders

Search for `package_name`, `PROJECT_NAME`, `AUTHOR_NAME`, and `CONTACT_EMAIL` before publishing a project created from this template.
