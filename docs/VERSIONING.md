# Versioning Policy

This document describes how SemVer Forge selects, stores, and synchronizes versions. It is project policy, not a universal rule imposed on every repository that uses the tool.

## 1. Version scheme

Use Semantic Versioning: `MAJOR.MINOR.PATCH`.

- **MAJOR:** incompatible public API or behavior changes.
- **MINOR:** backward-compatible functionality.
- **PATCH:** backward-compatible fixes and maintenance.

Pre-release identifiers may be used for alpha, beta, and release-candidate builds. Build metadata does not affect version precedence.

## 2. Canonical version source

The canonical version source is the source configured by `[version].source` in `.semver-forge.toml`. SemVer Forge supports different source types because projects do not all use the same build system or metadata layout.

Do not assume that `pyproject.toml`, `VERSION`, a package manifest, or a source-code constant is universally authoritative. The configured source is authoritative for the project being managed. Other version-bearing files belong in `[sync].targets` when they must mirror it.

For SemVer Forge itself, the canonical source is `project.version` in `pyproject.toml`. The root `VERSION` file, the package's `__version__`, and the Termux manifest fallback are synchronized representations of that version. The Termux build script also derives its package version from the root `VERSION` file.

## 3. Synchronization rules

Before changing SemVer Forge's own version, inspect the configured canonical source and every current-version representation:

- `pyproject.toml` → `project.version` (canonical for this repository)
- `VERSION` (synchronization target)
- `src/semver_forge/__init__.py` → `__version__`
- `packaging/termux/semver-forge.yaml` → fallback package version
- CLI `--version` output and built package metadata

Keep those values aligned. Do not replace historical versions in changelog entries, tests, examples, or documentation simply because they resemble current version values. A version-like string is not automatically a version source.

For other projects, follow their configured `[version].source` and `[sync].targets`; do not copy SemVer Forge's own source layout as a universal convention.

## 4. Change classification

| Change | Typical bump |
|---|---|
| Internal bug fix with compatible behavior | PATCH |
| Documentation-only correction | PATCH only when the project chooses to version documentation changes |
| New backward-compatible public feature | MINOR |
| New optional public API | MINOR |
| Removed or renamed public API | MAJOR |
| Incompatible behavior or configuration change | MAJOR |
| Security fix | PATCH unless compatibility requires otherwise |

The highest qualifying impact from the configured commit rules determines the proposed increment. The project may override the default classification through its configuration.

## 5. Changelog

Every published release version must have a corresponding `CHANGELOG.md` entry. Preserve historical entries. An `[Unreleased]` section may be used for changes that have not shipped.

## 6. Release status

The public SemVer Forge CLI currently exposes only `init`, `next`, and `sync`. Release execution and publishing are disabled. Retained release-planning code and `[release]` configuration fields do not authorize a release operation and must not be documented as an active workflow.

CI and packaging workflows are responsible for tests, builds, artifact inspection, and package installation checks. A release process must not be treated as available until release execution is explicitly re-enabled and its safety requirements are implemented and tested.
