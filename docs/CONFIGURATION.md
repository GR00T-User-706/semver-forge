# Configuration reference

SemVer Forge merges configuration from three scopes, in increasing precedence:
- System: `/etc/svfconfig`, or `$PREFIX/etc/svfconfig` when `PREFIX` is set (Termux).
- User: `~/.svfconfig`.
- Project: `.semver-forge.toml` (preferred), or `semver-forge.toml` (supported legacy name).

Project configuration filenames are mutually exclusive. If both project names exist, SemVer Forge reports the duplicate and stops rather than silently choosing one. Higher-precedence scopes override lower-precedence values. Nested tables merge recursively; arrays, including `sync.targets`, are replaced by the higher-precedence scope. Files such as `pyproject.toml`, `package.json`, `Cargo.toml`, and `PKGBUILD` are project metadata/version sources, not alternate SemVer Forge configuration files.

Unknown keys are reported by `config` and `check`; malformed TOML and invalid effective version settings are errors.

- `[project] name`, `description`: descriptive metadata.
- `[version] initial`: discovered starting version, or `0.1.0` only when no usable version source exists. `source`: inline table with `type`, `file`, optional `key`.
- `[git] tag_prefix`: commonly `v` or empty. `require_clean`: require clean tree. `baseline`: optional commit/tag boundary used only when no valid release tag exists. `unknown_commit`: `ignore` by default. `merge_commits`: reserved policy field; current implementation relies on Git's default log traversal.
- `[commits] breaking_changes`, `ignored_types`, `unknown`, `[commits.types]`: impact mapping; accepted impacts are `major`, `minor`, `patch`.
- `[sync] targets`: array of inline tables each with `type`, `file`, optional `key`.

Legacy `[release]` settings may remain in older configuration files, but release execution is disabled and the CLI does not use those settings. Newly generated configurations omit the section entirely.

Version source adapters: `text` (whole file), `json` (dotted `key`, defaults to `version`), `toml` (dotted `key`, defaults to `project.version`), `yaml` (dotted `key`, defaults to `version`), `shell` (one assignment; defaults to `VERSION`), `debian` (one `Version:` field), and `debian-changelog` (the first standard Debian changelog package/version header). TOML and YAML updates replace only the selected key's value and preserve unrelated content; YAML uses a round-trip parser to retain comments. The canonical source and targets are validated before synchronization.

## Discovery during initialization

`semver-forge init` inspects existing project metadata before generating configuration. It currently recognizes Python project metadata in `pyproject.toml`, Node metadata and scripts in `package.json`, Rust package metadata in `Cargo.toml`, plain version files, Debian changelog versions, and Arch `PKGBUILD` `pkgver` values. It uses README text as a description fallback and the directory name as a project-name fallback.

Initialization does not infer or configure test commands, build commands, or artifact paths. Tests and builds belong to CI and the project's packaging workflow, not SemVer Forge version policy.

If multiple recognized version sources disagree, initialization stops and reports the conflicting files. If no valid source exists, it creates `VERSION` at `0.1.0`. Existing project files are not rewritten during initialization.

## Recursive synchronization discovery

`semver-forge sync --discover` recursively scans the project for supported metadata files and adds them to the synchronization targets for that invocation. It recognizes the supported version filenames already used by initialization, including nested Python, Node, Rust, plain-text, Debian changelog, and Arch PKGBUILD metadata, plus YAML files with exactly one recognized version field (`control.Version`, `version`, or `package.version`). Ambiguous or invalid files are skipped rather than guessed. Discovered targets are merged with configured targets and persisted to the project configuration before synchronization. The merge is deduplicated by `(file, type, key)` and is idempotent. Discovery failures or configuration write failures stop before synchronization. With `--dry-run`, the proposed configuration and metadata changes are shown without writing either.


## Configuration commands

`semver-forge config` lists all scopes, the effective merged configuration, and the source scope for each effective value. Use `config get KEY`, `config set KEY TOML_VALUE`, or `config unset KEY`. The default write scope is project. Select `--global` or `--system` to write another scope. `config --edit` opens the selected file with `VISUAL`, then `EDITOR`, then `vi`.

Read operations never create files. Write operations create missing parent directories, validate TOML and effective required settings, and use an atomic replacement. Existing comments and unrelated values are retained when setting or unsetting a key. Arrays replace lower-scope arrays rather than being concatenated.

## Read-only check

`semver-forge check` reports the canonical version and source, configured synchronization targets and their actual values, target drift/missing/invalid/conflicting states, discovered supported metadata and whether it is configured, and the configuration scope files and effective settings. It does not synchronize or write any files. Use `--json` for machine-readable output.
