# Versioning Policy

This document defines the project's version scheme, source of truth, synchronization requirements, and release rules.

## 1. Scheme

Use Semantic Versioning: `MAJOR.MINOR.PATCH`.

- **MAJOR:** incompatible public API or behavior changes.
- **MINOR:** backward-compatible functionality.
- **PATCH:** backward-compatible fixes and maintenance.

Pre-release identifiers may be used for alpha, beta, and release-candidate builds. Build metadata must not be used to communicate precedence.

## 2. Canonical Version Source

For projects using PEP 621 metadata, the default canonical version source is `project.version` in `pyproject.toml`.

If dynamic versioning is intentionally adopted, document the actual source and mechanism here. Do not maintain competing version authorities.

The package should expose a matching `__version__` where practical. Build metadata, CLI output, and release tags must derive from or match the canonical source.

## 3. Synchronization

Before changing a version, inspect `pyproject.toml`, `src/<package_name>/__init__.py`, `VERSION` if present, CLI version output, package metadata, release workflow/tag conventions, and intentional current-version references. Do not blindly replace every version-like string. Historical changelog entries and examples are not current version sources.

## 4. Change classification

| Change | Typical bump |
|---|---|
| Internal bug fix with compatible behavior | PATCH |
| Documentation-only correction | PATCH if project policy versions docs |
| New backward-compatible public feature | MINOR |
| New optional public API | MINOR |
| Removed/renamed public API | MAJOR |
| Incompatible behavior/configuration change | MAJOR |
| Security fix | PATCH unless compatibility requires otherwise |

## 5. Changelog

Every release version must have a corresponding `CHANGELOG.md` entry. Keep an `[Unreleased]` section if used. Do not rewrite release history.

## 6. Git tags and releases

Use tags in the project's established format, normally `vMAJOR.MINOR.PATCH`. A release tag must point to the exact commit whose artifacts are published.

## 7. Release checklist

- [ ] Canonical version updated.
- [ ] Package-exposed version synchronized.
- [ ] Changelog entry present.
- [ ] Tests and lint checks completed.
- [ ] Source distribution and wheel built.
- [ ] Artifacts inspected and installed in a clean environment.
- [ ] Tag matches the release version.
- [ ] Release notes accurately describe shipped changes.
