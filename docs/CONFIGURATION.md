# Configuration reference

Semantic Version Forge reads TOML configuration from three scopes, in increasing
precedence:

1. **System:** `/etc/svfconfig`, or `$PREFIX/etc/svfconfig` in Termux.
2. **User:** `~/.svfconfig`.
3. **Project:** `.semver-forge.toml` (preferred), or `semver-forge.toml`
   (supported legacy filename).

Higher-precedence values override matching lower-precedence values. Nested
tables merge recursively. Arrays are replaced as a whole by the higher scope;
they are not concatenated. Project configuration filenames are mutually
exclusive. If both project filenames exist, SemVer Forge reports the duplicate
and stops.

This document explains the TOML syntax used by SemVer Forge and the
application-specific settings. For the complete language specification, see
[TOML v1.0.0](https://toml.io/en/v1.0.0/). The installed manual is
`man svf-config`.

## TOML syntax

A TOML file is made of key/value assignments and tables. A table header uses
square brackets. Keys below a header belong to that table until another header
appears.

```toml
[project]
name = "example-project"
description = "An example application"

[git]
tag_prefix = "v"
require_clean = true
```

The notation `git.tag_prefix` is a dotted reference to the `tag_prefix` key
inside the `[git]` table. It is useful for CLI operations such as
`svf config get git.tag_prefix`; it is not a requirement to write dotted keys
in the TOML file.

### Strings

Strings must be quoted. Use double quotes for basic strings:

```toml
name = "example-project"
```

Single-quoted literal strings are useful when backslashes should not be
interpreted as escapes:

```toml
path = 'relative/path with spaces'
```

TOML does not expand shell variables such as `$HOME`, and it does not expand
the `~` home-directory shortcut.

### Booleans

Booleans are unquoted lowercase values:

```toml
require_clean = true
breaking_changes = false
```

### Arrays

Arrays use square brackets and comma-separated values:

```toml
ignored_types = ["docs", "style", "test", "chore"]
```

Trailing commas are allowed. The value type must match the setting.

### Inline tables

An inline table groups related key/value pairs between braces:

```toml
source = { type = "toml", file = "pyproject.toml", key = "project.version" }
```

SemVer Forge uses inline tables for `version.source` and each item in
`sync.targets`.

### Arrays of inline tables

Synchronization targets are represented as an array of inline tables:

```toml
[sync]
targets = [
  { type = "text", file = "VERSION" },
  {
    type = "yaml",
    file = "packaging/termux/manifest.yaml",
    key = "control.Version",
  },
]
```

Each target requires `type` and `file`. The optional `key` selects a value
inside a structured format when needed.

### Comments and whitespace

A `#` begins a comment outside a quoted string. Blank lines and indentation
are for readability. Keep comments outside inline tables.

### Paths

Paths must resolve within the project root. Prefer relative paths so the
configuration is portable. TOML itself does not expand environment variables
or home-directory shortcuts. The configured adapter resolves the path when it
reads or updates the file.

## Configuration schema

The defaults below reflect the current configuration loader. Optional values
can be omitted to use their defaults.

### `[project]`

| Key | Type | Default | Meaning |
|---|---|---|---|
| `name` | string | unset | Optional project name used in reports. |
| `description` | string | `""` | Optional project description. |

### `[version]`

| Key | Type | Default | Meaning |
|---|---|---|---|
| `initial` | SemVer string | `"0.1.0"` | Starting version when no existing usable version source is discovered. Must parse as Semantic Versioning. |
| `source.type` | string | `"text"` | Adapter used to read and write the canonical version. |
| `source.file` | string | `"VERSION"` | Non-empty path to the canonical version file. |
| `source.key` | string | adapter-dependent | Optional dotted key or variable name for structured formats. |

The supported source types are:

| Type | Behavior | Default key |
|---|---|---|
| `text` | The whole file contains the version. | Not used |
| `json` | Read or update a JSON value. | `version` |
| `toml` | Read or update a TOML value. | `project.version` |
| `yaml` | Read or update a YAML value. | `version` |
| `shell` | Read or update one shell-style variable assignment. | Adapter variable default |
| `debian` | Read or update the unique Debian `Version:` field. | Not used |
| `debian-changelog` | Read or update the first standard Debian changelog version header. | Not used |

For JSON, TOML, and YAML, `key` is a dotted path through nested mappings.
For shell, it identifies the variable. The text and Debian adapters do not
use a dotted key.

Example:

```toml
[version]
initial = "1.2.3"
source = {
  type = "toml",
  file = "pyproject.toml",
  key = "project.version",
}
```

### `[git]`

| Key | Type | Default | Meaning |
|---|---|---|---|
| `tag_prefix` | string | `"v"` | Prefix removed from Git tags before parsing their version. Use an empty string for unprefixed tags. |
| `require_clean` | boolean | `true` | Legacy release safety setting. The current `next` and `sync` commands do not enforce it because release execution is disabled. |
| `baseline` | string or unset | unset | Optional commit or tag history boundary used when no valid release tag is available. `next` updates the saved baseline after processing history. |
| `unknown_commit` | string | `"ignore"` | Policy for unrecognized commit messages/types. Accepted values: `ignore`, `major`, `minor`, `patch`. |
| `merge_commits` | string | `"ignore"` | Reserved. The current Git history traversal does not apply a separate merge-commit policy, so changing this has no effect. |

### `[commits]`

| Key | Type | Default | Meaning |
|---|---|---|---|
| `breaking_changes` | boolean | `true` | When enabled, a Conventional Commit `!` marker or `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer produces a major impact. |
| `ignored_types` | array of strings | `["docs", "style", "refactor", "test", "build", "ci", "chore"]` | Commit types excluded from version impact classification. |
| `unknown` | string | `"ignore"` | Legacy fallback for unrecognized commits. The current planner takes this policy from `git.unknown_commit`, which has precedence. Configure that setting instead. |

### `[commits.types]`

Each key maps a Conventional Commit type to one impact value. Accepted
impacts are `major`, `minor`, and `patch`.

| Key | Default impact |
|---|---|
| `feat` | `minor` |
| `fix` | `patch` |
| `perf` | `patch` |
| `revert` | `patch` |

Additional commit types can be mapped:

```toml
[commits.types]
feat = "minor"
fix = "patch"
security = "patch"
docs = "patch"
```

Breaking-change markers take precedence when `breaking_changes = true`.
Types listed in `ignored_types` do not produce an impact.

### `[sync]`

| Key | Type | Default | Meaning |
|---|---|---|---|
| `targets` | array of inline tables | `[]` | Additional version fields to synchronize. Each item requires `type` and `file`; `key` is optional when the adapter has a default. |

Target types are the same adapters listed under `version.source.type`.
The canonical version source is synchronized in addition to the targets in
this array. TOML and YAML updates replace only the selected value and preserve
unrelated content; YAML uses a round-trip parser to retain comments.

Example:

```toml
[sync]
targets = [
  { type = "text", file = "VERSION" },
  { type = "yaml", file = "packaging/termux/manifest.yaml", key = "control.Version" },
  { type = "toml", file = "pyproject.toml", key = "project.version" },
]
```

### `[release]` legacy settings

These keys remain in the defaults for compatibility with older configuration
files. Release execution is disabled in the current CLI, so these settings do
not affect the public `svf` commands.

| Key | Type | Default | Former meaning |
|---|---|---|---|
| `commit_version` | boolean | `true` | Whether release version changes were committed. |
| `annotated_tag` | boolean | `true` | Whether a release Git tag was annotated. |
| `notes_file` | string | `"CHANGELOG.md"` | Release notes destination. |
| `require_confirmation` | boolean | `true` | Whether release execution required confirmation. |
| `release_when_no_changes` | boolean | `false` | Whether a release could be created without a classified version impact. |

Newly generated configurations omit this section.

## Editing and validating configuration

You can edit `.semver-forge.toml` with any text editor. Keep each key under
the correct table, quote strings, use lowercase booleans, and use square
brackets for arrays. A key under the wrong table is a different TOML key.

Useful commands:

```sh
svf config                 # print the selected TOML file as stored
svf config --list          # grouped settings, descriptions, and defaults
svf config --edit          # open VISUAL, EDITOR, or vi
svf config get git.tag_prefix
svf config set git.tag_prefix '"v"'
svf config set git.require_clean true
svf config set commits.ignored_types '["docs", "test"]'
svf config unset git.baseline
svf check                  # read-only project/configuration inspection
```

The value passed to `config set` must itself be a valid TOML value. For
example, a string needs TOML quotes inside the shell argument:
`svf config set git.tag_prefix '"v"'`.

Reads do not create files. Writes preserve unrelated TOML text, validate the
resulting TOML and effective required settings, and use atomic replacement.
The plain `svf config` command prints the selected file as stored and does not
validate it. Use `svf check` to parse the effective configuration and report
malformed TOML or invalid required settings without writing. The expanded
`svf config --verbose` report also loads the merged scopes.

For command syntax and options, see [the CLI reference](CLI_REFERENCE.md) or
`man svf`. For the configuration syntax and schema in the installed system,
see `man svf-config`.
