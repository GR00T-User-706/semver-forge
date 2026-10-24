# Security

Release requires a clean working tree and attached branch. Paths for version files must remain inside project root. File writes use temporary files and atomic replacement; synchronization restores prior bytes if a write or verification fails. An exclusive lock serializes releases. Tags are checked before creation and never moved. No remote push/publish is performed.

Configured command strings execute through a shell; only use trusted configuration. Prefer `args = ["tool", "arg"]` arrays. Do not put credentials in command arguments, environment values, stdout/stderr, changelogs, or release notes. Environment values configured in TOML are passed to subprocesses and are not intentionally printed. Stale locks require manual review. This is local release tooling, not a sandbox for untrusted configuration.
