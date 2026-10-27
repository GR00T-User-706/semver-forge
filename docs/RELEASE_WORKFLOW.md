# Release workflow

SemVer Forge owns version planning, version-file synchronization, changelog generation, and local Git release tags. It does **not** run project tests, build packages, collect artifacts, or publish packages. Those jobs belong to the project's CI pipeline and packaging tool (such as PKGforge).

1. Commit all intended changes and ensure the tree is clean.
2. Run `semver-forge doctor`, `status`, `next --explain`, and `release --dry-run`.
3. Run the project's tests and build independently, using its documented commands or CI workflow.
4. If you want to prepare the changelog separately, run `semver-forge changelog`, review the new version section, and commit the changelog update. Use `semver-forge changelog --dry-run` to preview without writing. The release command requires a clean working tree.
5. Run `semver-forge release` or an explicit bump.
6. Inspect the synchronization report and run `semver-forge verify-release`.

The boundaries are deliberate:

- **Plan:** calculate the next version from commit history.
- **Sync:** write the selected version to the configured version-bearing files.
- **Changelog:** preview release notes from commits.
- **Release:** update the changelog, optionally commit synchronized files, and create a local Git tag.
- **Build/package:** handled outside SemVer Forge.
- **Publish:** handled outside SemVer Forge.

If synchronization fails, SemVer Forge rolls back the version targets it already wrote. If a later Git operation fails, inspect `git status`, the configured targets, changelog, and tag list. Existing tags are never replaced.
