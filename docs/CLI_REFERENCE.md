# CLI Reference

SemVer Forge exposes five project commands.

## Global options

- `--project DIR`: select the project directory.
- `--json`: emit JSON output.
- `--version`: print the installed program version.

## Commands

| Command | Behavior |
|---|---|
| `init [--yes]` | Discover the project's canonical version source and synchronization targets, then create `.semver-forge.toml`. Existing configuration is preserved unless replacement is explicitly approved. |
| `next [--yes] [--explain]` | Analyze Git commits since the last processed history boundary. Select the highest qualifying SemVer impact, update the canonical version source plus configured targets, and write the corresponding release notes to the configured changelog. Save the processed commit boundary so the same commits are not counted twice. |
| `sync [--version VERSION] [--yes] [--discover] [--key KEY]` | Synchronize configured metadata. `--discover` persists newly discovered targets in project configuration before syncing. `--key` adds a custom assignment key to the discovery scan and may be repeated. |
| `config [get KEY | set KEY VALUE | unset KEY] [--global | --system] [--edit] [--yes]` | View or manage system, user, and project configuration. Project is the default write scope. |
| `check` | Read-only report of canonical version, synchronization targets, discovered metadata, and configuration scopes. |

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

After a successful run, the current Git commit is saved as the new baseline. This prevents the same commits from causing another increment on the next invocation. When the version changes, `next` also writes the calculated release notes to the configured `release.notes_file` (default `CHANGELOG.md`). Without `--yes`, `next` displays the planned version, synchronization targets, and changelog path and asks for authorization before writing. `--yes` authorizes the operation without prompting.

### sync

Synchronization is independent of commit classification. It copies the selected version to the canonical source and configured targets. Without `--yes`, `sync` displays the target version and any discovered configuration targets and asks for authorization before writing. `--yes` authorizes the operation without prompting.

Use `sync --discover` to scan nested project directories for supported version metadata, including YAML manifests with one unambiguous version field. The scan skips Git internals, virtual environments, dependency trees, and generated build directories. Discovered targets are deduplicated and persisted to project `[sync].targets` before synchronization. The interactive authorization occurs after discovery and before either configuration or metadata is written. Custom keys can be configured with `[sync].discovery_keys = ["SME_VERSION"]` or supplied directly with `--key SME_VERSION`. A custom key is searched as a literal assignment in readable UTF-8 text files; an unambiguous SemVer value becomes a shell-style target. Multiple valid assignments for the same key in one file are treated as ambiguous and ignored.

YAML synchronization uses a round-trip parser and updates only the configured dotted key while preserving comments and unrelated fields.

## Configuration

The project configuration is `.semver-forge.toml`. The command is `svf`; the Python distribution remains `semver-forge`. See [the example](../config/semver-forge.example.toml), [configuration guide](CONFIGURATION.md), and the installed `svf-config(5)` manual for TOML syntax and schema.

Mutating commands require write authorization by default. The effective
`[authorization].require_confirmation` setting can be set to `false` when
a trusted local workflow should bypass interactive confirmation. The `--yes`
option remains available for one-off bypasses. Discovery commands still report
what they found before writing; the configuration override controls whether the
final authorization prompt is required.


### config

The precedence order is system, global/user, project. System configuration is `/etc/svfconfig`, or `$PREFIX/etc/svfconfig` in Termux; global configuration is `~/.svfconfig`; project configuration is `.semver-forge.toml` (or the supported legacy filename). Nested tables merge; arrays are replaced by higher-precedence scopes.

```sh
svf config
svf config get commits.types.feat
svf config set commits.types.feat '"minor"'
svf config --global set git.tag_prefix '"v"'
svf config --system --edit
```

Reads do not create files. Configuration writes require interactive authorization by default; use `--yes` to authorize without prompting. Writes preserve unrelated TOML content, validate the resulting TOML and effective required settings, create missing parent directories, and atomically replace the selected file.

### check

`check` is read-only. It reports canonical source/version, every configured target and its state, discovered supported metadata, configuration scope files, precedence, effective values, source scopes, unknown keys, and readable errors. It performs no synchronization and makes no changes. Add `--json` for machine-readable output.
