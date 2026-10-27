# Configuration reference

SemVer Forge reads one project configuration file from the repository root:

- `.semver-forge.toml` (preferred), or
- `semver-forge.toml` (supported legacy name).

Do not keep both. If both exist, SemVer Forge reports the duplicate and stops instead of silently choosing one. `pyproject.toml`, `package.json`, `Cargo.toml`, `PKGBUILD`, and similar files are **project metadata/version sources**, not alternate SemVer Forge configuration files. They may coexist with the one SemVer Forge settings file.

## Settings

- `[project]`: project name and description.
- `[version]`: `initial` and canonical `source` (a table with `type`, `file`, and optional dotted `key`).
- `[git]`: tag prefix, clean-tree policy, optional baseline, and unknown-commit policy.
- `[commits]`: breaking-change behavior, ignored commit types, and the type-to-impact mapping.
- `[sync]`: the list of additional files that must carry the same version.
- `[release]`: local release behavior, changelog path, commit behavior, and tag style.

There are no test-command, build-command, or artifact-path settings. SemVer Forge does not build or test the project during a release. Run those through CI or your package builder.

## Adding synchronization targets as a project grows

Every target is an entry in `[sync].targets`. Each entry describes one version-bearing file:

- `type`: file format adapter.
- `file`: path relative to the project root.
- `key`: dotted key or variable name when the format needs one.

Example:

```toml
[sync]
targets = [
  { type = "text", file = "VERSION" },
  { type = "json", file = "package.json", key = "version" },
  { type = "toml", file = "pyproject.toml", key = "project.version" },
  { type = "shell", file = "packaging/arch/PKGBUILD", key = "pkgver" },
  { type = "debian-changelog", file = "debian/changelog" },
]
```

Add another entry whenever the project gains a new manifest, launcher, package recipe, or other file that must display the current version. Use the path from the repository root. Do not add historical changelog entries, examples, lockfiles, or files that merely mention a version. Add only files that SemVer Forge should actively rewrite.

Before using a new target, verify that its adapter supports both reading and writing. Run:

```sh
semver-forge sync --dry-run
semver-forge check
```

The dry run validates every configured source and target before any write. A missing file, unsupported format, invalid version, or conflicting value stops synchronization. Keep exactly one canonical source; list all mirrors under `sync.targets`.

## Initialization and discovery

`semver-forge init` scans recognized project manifests and version files, including Python `pyproject.toml`, Node `package.json`, Rust `Cargo.toml`, plain `VERSION` files, Debian changelogs, and Arch `PKGBUILD` version assignments. It reports every recognized version candidate. If candidates disagree, initialization stops and prints the files and values that conflict. Resolve the disagreement yourself, then run init again.

If no usable version source exists, init creates a plain `VERSION` file starting at `0.1.0`. Existing project metadata is not rewritten during discovery.

The configuration parser validates the SemVer Forge TOML file. The version adapters support plain text, JSON, TOML, shell assignments, Debian control version fields, and Debian changelog headers. YAML is not currently a supported version adapter.
