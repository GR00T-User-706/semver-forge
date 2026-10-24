# Troubleshooting

- `not inside a Git repository`: pass `--project PATH` or run within a repository.
- Dirty-tree refusal: commit/stash staged, unstaged, and untracked files.
- No config: run `semver-forge init`, then review the generated file.
- No release-relevant commits: use an explicit bump or configure policy; no automatic no-op release is created by default.
- Ambiguous tags: manually resolve duplicate tags that map to the same SemVer precedence; the tool will not guess.
- YAML/TOML write unsupported: use a text/JSON/shell/Debian adapter, or implement and configure an explicit adapter.
- Existing lock: verify no release process is active before removing `.git/semver-forge.lock`.
- Test/build failures: inspect captured command stderr and correct the project-owned command configuration.
