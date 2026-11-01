# SemVer Forge

Automatic project version tracking. SemVer Forge has exactly three project commands:

- `init`: initialize version tracking.
- `next`: inspect Git history, choose the correct SemVer increment, and update configured version files.
- `sync`: synchronize configured metadata to the current canonical version.

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

An explicit target version can be supplied with `--version VERSION`.

## Configuration

The project configuration is `.semver-forge.toml`. The canonical source and synchronization targets are defined there. See [the example configuration](config/semver-forge.example.toml) and [configuration reference](docs/CONFIGURATION.md).

## Versioning rules

Conventional Commit types are classified using the project's configured `[commits.types]` table. Breaking changes take precedence over features, and features take precedence over fixes. Unrecognized and ignored commit types do not trigger a version change by default.

Git is required for `next`, because commit history is the input to version selection. `init` can create project configuration without Git, but automatic version selection requires a Git repository.

## Tests

Run the test suite with:

```sh
./tests/run-tests.sh
```
