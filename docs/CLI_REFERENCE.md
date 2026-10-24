# CLI Reference

Run `semver-forge --help` for the command index and
`semver-forge COMMAND --help` for command-specific help.

## Global options

- `--version`: print the program version.
- `--project DIR`: select a project directory.
- `--json`: request JSON output where supported.

## Commands

| Command | Behavior |
|---|---|
| `init [--yes]` | Generate project configuration and VERSION if missing. Existing config requires approval. On Git repositories, stage only generated files and commit them if the index is clean. |
| `doctor` | Inspect Python, Git, repository state, configuration, and version source. |
| `current` | Show canonical version and source. |
| `validate VERSION` | Validate a SemVer version. |
| `compare A B` | Compare versions by SemVer precedence. |
| `bump patch\|minor\|major` | Calculate an increment; `--write` synchronizes targets. |
| `next [--explain]` | Calculate the next version from commits since the release boundary. |
| `sync [--version VERSION] [--dry-run]` | Synchronize configured version sources. |
| `status`, `history`, `check` | Inspect repository and version state. |
| `changelog` | Print generated release notes. |
| `release [part]` | Prepare and create a local release. |
| `verify-tag`, `verify-release` | Verify the latest recognized SemVer tag. |
| `install`, `uninstall` | Manage the user-local installation. |

## Initialization behavior

Git is optional for creating project configuration. In a Git repository,
generated files are staged by explicit path and committed with
`chore(init): initialize SemVer Forge project configuration` when the index
has no pre-existing staged changes. A configured remote is pushed after a
successful local commit; push failure preserves the local commit. Existing
configuration is never overwritten without interactive approval or `--yes`.
An existing VERSION file is preserved.

## Logging and VCS

SemVer Forge writes its own bounded diagnostic log under the user's local state
directory. It does not manage project-maintainer log files or their Git tracking
policy. Git is the only supported VCS backend currently; other backends require
future implementations.

## Safety

Real releases require a clean working tree by default. Existing tags are never
moved or overwritten. Configured command hooks may execute code and should be
reviewed before use. TOML writing and bundled YAML parsing are not implemented.
