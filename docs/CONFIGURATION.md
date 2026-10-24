# Configuration reference

Configuration file: `.semver-forge.toml` or `semver-forge.toml` at repository root. Unknown keys are warned about; malformed TOML and invalid initial versions are errors.

- `[project] name`, `description`: descriptive metadata.
- `[version] initial`: fallback/policy version (currently used as configuration metadata; initialize `VERSION` explicitly). `source`: inline table with `type`, `file`, optional `key`.
- `[git] tag_prefix`: commonly `v` or empty. `require_clean`: require clean tree. `baseline`: optional commit/tag boundary used only when no valid release tag exists. `unknown_commit`: `ignore` by default. `merge_commits`: reserved policy field; current implementation relies on Git's default log traversal.
- `[commits] breaking_changes`, `ignored_types`, `unknown`, `[commits.types]`: impact mapping; accepted impacts are `major`, `minor`, `patch`.
- `[sync] targets`: array of inline tables each with `type`, `file`, optional `key`.
- `[release] commit_version`, `annotated_tag`, `notes_file`, `require_confirmation`, `release_when_no_changes`, `test_commands`, `build_commands`, `artifact_paths`.

Commands may be configured as strings (shell execution) or tables with `args = ["program", "arg"]`, `cwd`, `timeout`, and `env`. Prefer `args` to avoid shell interpretation. Current release flow runs configured tests automatically; build commands run only with `release --build`. `require_confirmation` is retained as policy metadata; this CLI currently does not prompt interactively and expects an explicit command invocation. Use `--dry-run` first.

Version source adapters: `text` (whole file), `json` (dotted `key`, defaults to `version`), `toml` (read only; defaults to `project.version`), `shell` (one assignment; defaults to `VERSION`), and `debian` (one `Version:` field). `yaml` fails with actionable guidance until an adapter is supplied. The canonical source and targets are validated before synchronization. TOML write targets are currently unsupported.
