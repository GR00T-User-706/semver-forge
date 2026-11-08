# SemVer Forge Project Standards

These standards apply to SemVer Forge as a version-management and release-metadata tool. They supplement `AGENTS.md`, `CONTRIBUTING.md`, the CLI reference, configuration examples, and existing versioning documentation.

## Product boundary

SemVer Forge discovers project metadata, determines or validates semantic-version changes, and synchronizes version references according to configured rules. It is not a package builder and must not be documented as one.

Clearly distinguish:
- project version source discovery;
- version calculation or validation;
- changelog handling;
- synchronization of configured version targets;
- local Git operations;
- remote publication or release actions.

Do not imply that a stage runs automatically when it requires an explicit command or authorization.

## Version source and target documentation

Document the actual precedence used to identify a project's canonical version source. For each supported target, specify its file format, path/key or syntax, direction of synchronization, parsing rules, supported version forms, write behavior, and failure handling. Identify unsupported or ambiguous targets rather than guessing.

The `.semver-forge.toml` reference must cover every supported top-level section and nested field, including defaults, accepted values, path resolution, discovery behavior, sync targets, exclusions, and conflict/error behavior. Examples must match the current parser and schema.

## CLI contract

Keep command names, aliases, positional arguments, options, defaults, exit codes, and examples aligned with the real CLI parser. Document global help and per-command help. Explain whether a command is read-only, stages files, creates commits, or contacts a remote. Do not present a preview or dry run as a completed write.

## Changelog and SemVer policy

Explain how SemVer Forge reads and updates changelog formats, including supported heading/version syntax and preservation behavior. Keep the tool's own changelog separate from changelogs in projects it manages. Never invent a version bump from a documentation-only edit.

## Git and safety boundaries

Document all Git side effects and authorization requirements. Preserve the working tree and existing commits. Do not reset, discard, rewrite history, force-push, or push releases without explicit authorization. A failed remote operation must not be described as if local work was rolled back unless that was verified.

## Validation and documentation-only changes

Distinguish parser/config validation, version discovery, synchronization, local Git operations, and remote operations in test reports. Documentation-only changes do not require a version bump unless existing repository policy explicitly requires one; record them in the changelog without claiming implementation changes.
