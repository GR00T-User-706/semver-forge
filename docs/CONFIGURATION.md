# Configuration reference

Configuration file: `.semver-forge.toml` or `semver-forge.toml` at repository root. Unknown keys are warned about; malformed TOML and invalid initial versions are errors.

- `[project] name`, `description`: descriptive metadata.
- `[version] initial`: discovered starting version, or `0.1.0` only when no usable version source exists. `source`: inline table with `type`, `file`, optional `key`.
- `[git] tag_prefix`: commonly `v` or empty. `require_clean`: require clean tree. `baseline`: optional commit/tag boundary used only when no valid release tag exists. `unknown_commit`: `ignore` by default. `merge_commits`: reserved policy field; current implementation relies on Git's default log traversal.
- `[commits] breaking_changes`, `ignored_types`, `unknown`, `[commits.types]`: impact mapping; accepted impacts are `major`, `minor`, `patch`.
- `[sync] targets`: array of inline tables each with `type`, `file`, optional `key`.
- `[release] commit_version`, `annotated_tag`, `notes_file`, `require_confirmation`, `release_when_no_changes`, `test_commands`, `build_commands`, `artifact_paths`.

Commands may be configured as strings (shell execution) or tables with `args = ["program", "arg"]`, `cwd`, `timeout`, and `env`. Prefer `args` to avoid shell interpretation. Current release flow runs configured tests automatically; build commands run only with `release --build`. `require_confirmation` is retained as policy metadata; this CLI currently does not prompt interactively and expects an explicit command invocation. Use `--dry-run` first.

Version source adapters: `text` (whole file), `json` (dotted `key`, defaults to `version`), `toml` (dotted `key`, defaults to `project.version`), `shell` (one assignment; defaults to `VERSION`), and `debian` (one `Version:` field). TOML updates replace only the selected key's value and preserve surrounding text and comments. `yaml` fails with actionable guidance until an adapter is supplied. The canonical source and targets are validated before synchronization.

## Discovery during initialization

`semver-forge init` inspects existing project metadata before generating configuration. It currently recognizes Python project metadata in `pyproject.toml`, Node metadata and scripts in `package.json`, Rust package metadata in `Cargo.toml`, plain version files, Debian changelog versions, and Arch `PKGBUILD` `pkgver` values. It uses README text as a description fallback and the directory name as a project-name fallback.

It recognizes standard Python, Node, and Rust test/build commands, plus a restricted allowlist of known commands found in GitHub Actions workflow files. It never copies arbitrary workflow shell commands or executes commands during discovery. Artifact paths are inferred only for recognized build systems. Missing test/build/artifact information remains an empty list.

If multiple recognized version sources disagree, initialization stops and reports the conflicting files. If no valid source exists, it creates `VERSION` at `0.1.0`. Existing project files are not rewritten during initialization.
