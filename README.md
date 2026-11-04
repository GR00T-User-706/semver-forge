# SemVer Forge

Automatic project version tracking. SemVer Forge provides five project commands:

- `init`: initialize version tracking.
- `next`: inspect Git history, choose the correct SemVer increment, and update configured version files.
- `sync`: synchronize configured metadata to the current canonical version.
- `config`: inspect and manage system, user, and project configuration.
- `check`: inspect project version synchronization and configuration without writing.

There is no release or publishing workflow in this command interface.

## Install

SemVer Forge requires Python 3.10+ and Git.

```sh
python -m pip install .
svf --help
```

The package exposes `svf` as its primary executable and retains `semver-forge` as a compatibility alias. The Python distribution remains `semver-forge`. Existing pipx installations can be upgraded from the repository with `pipx install --force .`.

## Initialize a project

Run this from the project directory:

```sh
svf init
```

Initialization inspects existing project metadata, chooses a canonical version source, detects compatible synchronization targets, and writes `.semver-forge.toml`. Existing version values are preserved. Conflicting version sources must be resolved before initialization.

## Calculate and apply the next version

```sh
svf next
```

SemVer Forge inspects commits since the last processed Git boundary and applies the highest qualifying impact:

| Commit impact | Version change |
|---|---|
| Breaking change (`!` or `BREAKING CHANGE:`) | Major |
| `feat` | Minor |
| `fix`, `perf` | Patch |
| Docs, tests, style, refactor, build, CI, chore | No version change by default |

The command updates configured version files when a version change is warranted. It records the processed Git commit in `.semver-forge.toml`, so running `next` again does not count the same commits twice.

Preview without writing:

```sh
svf next --dry-run
```

## Synchronize metadata

```sh
svf sync
```

This copies the canonical version to configured targets. Preview first with:

```sh
svf sync --dry-run
```

To recursively discover supported version metadata in the project and synchronize it too:

```sh
svf sync --discover --dry-run
svf sync --discover
```

Discovery scans nested project directories for supported metadata files, including YAML manifests with an unambiguous version field. It skips Git internals, virtual environments, dependency trees, and generated build directories. Discovered targets are added to `[sync].targets` in project configuration before synchronization. The merge is deduplicated and idempotent. `--dry-run` previews both the configuration change and file synchronization without writing either. An explicit target version can be supplied with `--version VERSION`.

## Configuration

Configuration is layered in this order: system (`/etc/svfconfig`, or `$PREFIX/etc/svfconfig` in Termux), user (`~/.svfconfig`), then project (`.semver-forge.toml`, with `semver-forge.toml` supported as a legacy filename). Project values take precedence. Use `svf config` to print the project TOML, and `svf config --list` to list recognized keys. Use `--verbose` for scope and effective-value details. See [the example configuration](config/semver-forge.example.toml), [configuration reference](docs/CONFIGURATION.md), and `man svf-config` for TOML syntax and the complete schema.

Examples:

```sh
svf config
svf config --get commits.types.feat
svf config --set commits.types.feat '"minor"'
svf config --global --set git.tag_prefix '"v"'
svf config --system --edit
```

Reads do not create configuration files. Writes create parent directories as needed, validate TOML and effective required settings, preserve unrelated configuration text, and use atomic replacement. System-scope writes may require elevated permissions.

## Read-only diagnostics

```sh
svf check
svf check --json\nsemver-forge check --verbose\nsemver-forge check --debug
```

The default check output contains only the project name, version, and synchronized files. Use `--verbose` for the full report or `--debug` for diagnostic tracebacks. It never changes project files or configuration.

## Versioning rules

Conventional Commit types are classified using the project's configured `[commits.types]` table. Breaking changes take precedence over features, and features take precedence over fixes. Unrecognized and ignored commit types do not trigger a version change by default.

Git is required for `next`, because commit history is the input to version selection. `init` can create project configuration without Git, but automatic version selection requires a Git repository.

## Tests

Run the test suite with:

```sh
./tests/run-tests.sh
```
