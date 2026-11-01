# CLI Reference

SemVer Forge exposes exactly three project commands.

## Global options

- `--project DIR`: select the project directory.
- `--json`: emit JSON output.
- `--version`: print the installed program version.

## Commands

| Command | Behavior |
|---|---|
| `init [--yes]` | Discover the project's canonical version source and synchronization targets, then create `.semver-forge.toml`. Existing configuration is preserved unless replacement is explicitly approved. |
| `next [--dry-run] [--explain]` | Analyze Git commits since the last processed history boundary. Select the highest qualifying SemVer impact and update the canonical version source plus configured targets. Save the processed commit boundary so the same commits are not counted twice. |
| `sync [--version VERSION] [--dry-run] [--discover]` | Synchronize configured metadata to the canonical version, or to an explicitly supplied version. `--discover` also scans nested project directories for supported metadata. |

## Version selection

Default Conventional Commit rules:

| Commit | Result |
|---|---|
| Breaking change marker (`!` or `BREAKING CHANGE:`) | Major |
| `feat` | Minor |
| `fix`, `perf` | Patch |
| `docs`, `style`, `refactor`, `test`, `build`, `ci`, `chore` | No change |

The highest qualifying impact wins. Rules can be changed in `.semver-forge.toml`.

## Command behavior

### init

Initialization is project discovery and tracking setup. It does not calculate a new version. Existing version values are preserved. Conflicting recognized version sources stop initialization before files are written. Git is optional for initialization.

### next

This is the automatic version-selection command. It reads commits since the saved `[git].baseline`, or the latest valid SemVer tag when no baseline has been saved. It updates the canonical source and every configured synchronization target only when a qualifying commit warrants a higher version.

After a successful run, the current Git commit is saved as the new baseline. This prevents the same commits from causing another increment on the next invocation. A dry run does not write files or advance the baseline.

### sync

Synchronization is independent of commit classification. It copies the selected version to the canonical source and configured targets. Use `--dry-run` to preview all file changes before writing.

Use `sync --discover` to scan nested project directories for supported version metadata, including YAML manifests with one unambiguous version field. The scan skips Git internals, virtual environments, dependency trees, and generated build directories. Discovered targets are synchronized for that invocation only; the project configuration is not rewritten.

YAML synchronization uses a round-trip parser and updates only the configured dotted key while preserving comments and unrelated fields.

## Configuration

The project configuration is `.semver-forge.toml`. See [the example](../config/semver-forge.example.toml) and [configuration guide](CONFIGURATION.md).
