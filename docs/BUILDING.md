# Building and Packaging

## Build backend

This template uses setuptools with the PEP 517 build interface. The build frontend is `python -m build`.

## Development environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows, activate with `.venv\\Scripts\\activate`.

## Build wheel and source distribution

```bash
python -m pip install build
python -m build
```

Expected outputs:
- `dist/*.whl`: installable wheel.
- `dist/*.tar.gz`: source distribution.

## Inspect artifacts

```bash
python -m pip install --upgrade twine
python -m twine check dist/*
python -m zipfile -l dist/*.whl
tar -tzf dist/*.tar.gz
```

Test installation in a clean virtual environment. Test wheel and source distribution separately where practical.

## Build isolation and offline builds

PEP 517 build isolation normally installs declared build requirements into an isolated environment. For offline builds, ensure required build backend and dependencies are available in a local wheelhouse. Do not disable build isolation unless the environment is deliberately provisioned and the reason is understood.

## Dependency boundaries

- Runtime dependencies belong in `project.dependencies`.
- Development/test/build tools belong in optional dependency groups or documented build requirements.
- Do not include test suites, CI configuration, local secrets, virtual environments, or unrelated repository files in runtime distributions.
- Inspect wheel and sdist contents before release.

## Platform-specific packaging

Native installers, OS packages, containers, and standalone executables are optional project-specific layers. Add them only when needed and document supported targets, build host, prerequisites, exact commands, output artifacts, and validation procedure.

Python wheels are not universal executable installers. Consider platform and ABI compatibility for compiled extensions.
