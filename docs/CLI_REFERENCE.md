# CLI Reference

Run `semver-forge --help` for the command index and `semver-forge COMMAND --help` for command-specific help. A Unix man page is shipped at `man/semver-forge.1` and installed to `PREFIX/share/man/man1/semver-forge.1`.

## Global options

- `--version`: print the program version.
- `--project DIR`: select a project directory; defaults to discovery from the current directory.
- `--json`: request JSON output where supported.
- `-h`, `--help`: display help.

## Commands

| Command | Behavior | Writes by default? |
|---|---|---:|
| `init` | Create `.semver-forge.toml`; create `VERSION` only if missing. Refuses to overwrite existing config. | Yes, starter files |
| `doctor` | Inspect Python, Git, repository state, configuration, and canonical version source. | No |
| `current` | Show canonical version and source. | No |
| `validate VERSION` | Validate a SemVer 2.0.0 version. | No |
| `compare A B` | Compare versions by SemVer precedence; build metadata is ignored for precedence. | No |
| `bump patch\|minor\|major` | Calculate an increment; `--write` synchronizes configured targets and `--dry-run` previews. | Only with `--write` and without `--dry-run` |
| `next [--explain]` | Calculate the next version from commits since the release boundary. | No |
| `sync [--version VERSION] [--dry-run]` | Synchronize configured version sources. | Yes, unless `--dry-run` |
| `status` | Summarize repository state, current version, latest tag, and proposed next version. | No |
| `history` | Show commits since the release boundary. | No |
| `check` | Check that configured version sources agree. | No |
| `changelog [--dry-run]` | Preview generated notes. In this implementation the command prints notes; it does not update `CHANGELOG.md`. | No |
| `release [part]` | Prepare and create a local release. Options: `--version VERSION`, `--prerelease alpha\|beta\|rc`, `--dry-run`, `--notes-only`, `--yes`, `--build`. | Yes, unless dry-run/notes-only |
| `verify-tag` | Verify the latest recognized SemVer release tag. | No |
| `verify-release` | Verify the latest recognized tag and whether it points to `HEAD`. | No |
| `install [--prefix DIR]` | Install the source-tree package, launcher, and man page. | Installation prefix |
| `uninstall [--prefix DIR]` | Remove recognized installed files. | Installation prefix |

## Examples

```sh
semver-forge init
semver-forge doctor --json
semver-forge validate 1.2.3-rc.1+build.7
semver-forge compare 1.2.3 1.3.0
semver-forge next --explain
semver-forge sync --dry-run
semver-forge release --dry-run
semver-forge release patch --yes
semver-forge verify-release
```

## Important behavior

- Releases are local. No push or remote publishing command is implemented.
- Real releases require a clean working tree by default and refuse to overwrite an existing version tag.
- Tests are not treated as passed if no test commands are configured.
- A requested build fails when no build commands are configured.
- `--dry-run` previews release actions and must not update files, commits, or tags.
- Configured command hooks may execute code. Review configuration before use.
- TOML is readable as a version source but TOML writing is not implemented. YAML parsing is not bundled.
