# QA and Release Checklist

Use this as a starting point. Remove checks only after confirming they do not apply; add project-specific checks as the implementation grows.

## Repository and metadata
- [ ] Project name, import package, and metadata are consistent.
- [ ] Supported Python versions are accurate.
- [ ] Runtime and optional dependencies are correctly classified.
- [ ] No secrets, local environment files, or generated artifacts are tracked.
- [ ] License and package classifiers are accurate.

## Code quality
- [ ] `ruff check .` passes.
- [ ] `ruff format --check .` passes.
- [ ] Type checks pass if configured.
- [ ] No accidental debug code or dead placeholders remain.

## Tests
- [ ] `pytest` passes.
- [ ] Relevant edge cases and error paths are covered.
- [ ] Tests do not depend on undeclared local state.
- [ ] Supported Python versions are exercised in CI.

## Packaging
- [ ] `python -m build` succeeds.
- [ ] `python -m twine check dist/*` passes.
- [ ] Wheel and source distribution contents are inspected.
- [ ] Install and import work in a clean environment.
- [ ] Console entry points work, if provided.

## Security
- [ ] Inputs and filesystem paths are validated.
- [ ] Subprocess calls use safe argument handling.
- [ ] Secrets are not committed or logged.
- [ ] Deserialization and network boundaries are reviewed.
- [ ] Dependencies are checked for known vulnerabilities using chosen tooling.

## Release
- [ ] Version follows `docs/VERSIONING.md`.
- [ ] Changelog is updated.
- [ ] Documentation reflects shipped behavior.
- [ ] Artifacts correspond to the release commit.
- [ ] Known limitations are recorded.
