# Release workflow

1. Commit all intended changes and ensure the tree is clean.
2. Review `semver-forge doctor`, `status`, `next --explain`, and `release --dry-run`.
3. Configure test commands in `[release].test_commands`; configure build commands if needed.
4. Run `semver-forge release` or an explicit bump. Add `--build` to run configured build commands.
5. Inspect the final report and run `semver-forge verify-release`.

Calculating a version only predicts. Synchronization updates metadata. Release preparation creates notes and runs configured validation. Tagging creates a local Git reference. Building runs project-owned commands. Publishing means sending artifacts/tags to a remote provider; semver-forge does not currently publish.

If failure occurs after synchronization, inspect `git status`, the configured version targets, changelog, and tag list. Synchronization rolls back target files on a synchronization failure. Later failures are reported but do not automatically rewrite history or delete tags. Recover manually with a reviewed Git commit or restore from backups. Existing tags are never replaced.
