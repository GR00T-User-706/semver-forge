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
semver-forge --help
```

The package exposes the `semver-forge` executable through its `pyproject.toml` entry point. Existing pipx installations can be upgraded from the repository with `pipx install --force .`.

## Initialize a project

Run this from the project directory:

```sh
semver-forge init
```

Initialization inspects existing project metadata, chooses a canonical version source, detects compatible synchronization targets, and writes `.semver-forge.toml`. Existing version values are preserved. Conflicting version sources must be resolved before initialization.

## Calculate and apply the next version

```sh
semver-forge next
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
semver-forge next --dry-run
```

## Synchronize metadata

```sh
semver-forge sync
```

This copies the canonical version to configured targets. Preview first with:

```sh
semver-forge sync --dry-run
```

To recursively discover supported version metadata in the project and synchronize it too:

```sh
semver-forge sync --discover --dry-run
semver-forge sync --discover
```

Discovery scans nested project directories for supported metadata files, including YAML manifests with an unambiguous version field. It skips Git internals, virtual environments, dependency trees, and generated build directories. Discovered targets are added to `[sync].targets` in project configuration before synchronization. The merge is deduplicated and idempotent. `--dry-run` previews both the configuration change and file synchronization without writing either. An explicit target version can be supplied with `--version VERSION`.

## Configuration

Configuration is layered in this order: system (`/etc/svfconfig`, or `$PREFIX/etc/svfconfig` in Termux), user (`~/.svfconfig`), then project (`.semver-forge.toml`, with `semver-forge.toml` supported as a legacy filename). Project values take precedence. Use `semver-forge config` to inspect effective values and their source scopes. See [the example configuration](config/semver-forge.example.toml) and [configuration reference](docs/CONFIGURATION.md).

Examples:

```sh
semver-forge config
semver-forge config --get commits.types.feat
semver-forge config --set commits.types.feat '"minor"'
semver-forge config --global --set git.tag_prefix '"v"'
semver-forge config --system --edit
```

Reads do not create configuration files. Writes create parent directories as needed, validate TOML and effective required settings, preserve unrelated configuration text, and use atomic replacement. System-scope writes may require elevated permissions.

## Read-only diagnostics

```sh
semver-forge check
semver-forge check --json
```

The check command reports the canonical version, configured target status, discovered metadata, configuration scopes, effective settings, source scopes, and unknown keys. It never changes project files or configuration.

## Versioning rules

Conventional Commit types are classified using the project's configured `[commits.types]` table. Breaking changes take precedence over features, and features take precedence over fixes. Unrecognized and ignored commit types do not trigger a version change by default.

Git is required for `next`, because commit history is the input to version selection. `init` can create project configuration without Git, but automatic version selection requires a Git repository.

## Tests

Run the test suite with:

```sh
./tests/run-tests.sh
```
