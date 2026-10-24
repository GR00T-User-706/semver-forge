# Changelog

All notable changes to this project are documented here.

This format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [0.2.0] - 2026-10-24

### Added
- Bounded local diagnostics for SemVer Forge operations, separate from project-maintainer logs.
- A version-control backend protocol with Git as the initial implementation.

### Fixed
- Initialization can run outside a Git repository and commits only its own generated files when the Git index is clean.
- Initialization preserves existing VERSION values and requires approval before replacing existing SemVer Forge configuration.

## [0.1.0] - YYYY-MM-DD

### Added
- Initial Python project template scaffold.
- PEP 517/518 build configuration and PEP 621 project metadata.
- Standard source layout, tests, documentation, and GitHub workflows.
