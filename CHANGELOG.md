# Changelog

All notable changes to this project are documented here.

This format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
- Discovery-first initialization derives project metadata, version sources, synchronization targets, test/build commands, artifact paths, and changelog conventions from recognized project files and CI workflows.
- Safe TOML version-field synchronization that preserves unrelated project metadata and comments.

### Fixed
- Initialization rejects conflicting recognized version sources instead of silently selecting one.
- Debian changelog headers are recognized and synchronized using their package/version header.
- Missing metadata in one manifest no longer blocks fallback discovery from later manifests.
- TOML version synchronization recognizes table headers with trailing comments.
- Initialization reports staging failures accurately, preserves unrelated staged changes, and pushes successful retry commits to configured remotes.

## [0.2.0] - 2026-10-24

### Added
- Bounded local diagnostics for SemVer Forge operations, separate from project-maintainer logs.
- A version-control backend protocol with Git as the initial implementation.

### Fixed
- Initialization can run outside a Git repository and commits only its own generated files without disturbing unrelated staged changes.
- Initialization preserves existing VERSION values and requires approval before replacing existing SemVer Forge configuration.

## [0.1.0] - YYYY-MM-DD

### Added
- Initial Python project template scaffold.
- PEP 517/518 build configuration and PEP 621 project metadata.
- Standard source layout, tests, documentation, and GitHub workflows.
