# Changelog

All notable changes to SemVer Forge are documented here.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- No unreleased changes are recorded yet.

## [0.2.0] - 2026-10-24

### Added
- Project initialization and discovery across Python, Node.js, Rust, and generic repositories.
- Detection of project identity, existing version sources, synchronization targets, test/build commands, artifact paths, and changelog conventions.
- Semantic release planning from Git history, including Conventional Commit impact rules and breaking-change handling.
- Version synchronization for supported project metadata, including TOML manifests and Debian changelogs.
- Local release workflow with generated release notes, configured checks, version synchronization, and annotated Git tags.
- A version-control boundary with Git as the initial backend.
- Bounded user-local operation diagnostics.
- CLI commands for initialization, diagnostics, current version, status, history, validation, comparison, bumping, synchronization, changelog generation, release verification, installation, and removal.

### Changed
- Initialization now discovers project metadata before generating configuration and can operate outside a Git repository.
- Initialization stages and commits only files it generated, preserving unrelated staged changes.
- Existing VERSION values are preserved during discovery; conflicting recognized version sources are reported instead of silently choosing one.
- Configuration generation derives project-specific values rather than relying on a generic project template.
- Version synchronization validates targets before writing and preserves unrelated TOML structure and comments.
- Release operations require explicit authorization for writes and do not push releases to a remote.

### Fixed
- Initialization supports Python 3.10 through the `tomli` fallback when the standard-library TOML parser is unavailable.
- Discovery falls back when individual manifests lack usable project metadata.
- TOML table headers with trailing comments are handled during synchronization.
- Debian changelog version headers are recognized for supported SemVer-compatible versions.
- Initialization reports staging and commit failures separately and preserves local commits when a configured remote push fails.
- CLI output and documentation were brought into line with the implemented command behavior.
- Ruff lint and formatting findings were resolved without disabling lint rules.

## [0.1.0] - 2026-10-23

### Added
- Initial SemVer Forge project scaffold.
- Python package layout, build metadata, test configuration, documentation, and GitHub Actions workflows.

---

The 0.2.0 notes consolidate the implementation history into user-facing changes.
Individual formatting, lint-only, and intermediate development commits are intentionally
grouped under the feature or fix they contributed to rather than listed as separate release
entries.
