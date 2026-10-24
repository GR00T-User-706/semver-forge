# Release Process

1. Review requested release scope and current Git state.
2. Complete the read-only audit required by `AGENTS.md`.
3. Run tests, lint, type checks, and project-specific integration checks.
4. Inspect dependency declarations and security-sensitive changes.
5. Update the canonical version and all intentional mirrors.
6. Add the release entry to `CHANGELOG.md`.
7. Update user and developer documentation.
8. Build wheel and source distribution with `python -m build`.
9. Inspect artifacts and run `twine check`.
10. Test installation in a clean environment.
11. Review the final diff and confirm no unrelated files are included.
12. Create the version tag on the exact release commit.
13. Publish artifacts and release notes using the authorized process.
14. Verify published files, metadata, checksums, and release page.

Never publish from an unverified working tree. Do not claim a release is complete until published artifacts have been checked.
