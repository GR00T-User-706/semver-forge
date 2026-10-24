# AGENTS.md

This file defines the operating rules for any AI agent, coding assistant, automation, or human contributor working in this repository.

The short version: **do the requested work, preserve the project, update the version, update the docs, and do not rewrite the universe because someone asked for one function.**

## 1. Prime Directive

Make the smallest responsible change that fully satisfies the task. Avoid unnecessary rewrites, broad refactors, file renames, architecture swaps, dependency changes, or style churn unless the requested task clearly requires them.

Do not treat a narrow request as permission to redesign unrelated systems.

## 2. Project Identity

This is a reusable Python project template. A repository created from it may be a library, CLI, service, desktop application, automation tool, or another Python project. Project-specific goals, supported platforms, runtime behavior, and architecture must be documented by the project itself. Do not assume every project is a GUI, CLI, web service, or library.

## 3. Scope Control

Before changing files, identify the actual requested scope.

Good behavior:
- Read relevant files and project instructions first.
- Determine the smallest safe implementation path.
- Modify only files related to the task.
- Preserve existing public behavior unless the task requires changing it.
- Keep unrelated formatting changes out of the patch.
- Explain any necessary larger change before making it.

Bad behavior:
- Rewriting modules for a small feature.
- Renaming files without need.
- Reorganizing directories without need.
- Replacing working code because it is not your preferred style.
- Introducing dependencies without justification.
- Breaking existing behavior while chasing elegance.

## 4. No Rewrite-the-Universe Rule

A full rewrite is forbidden unless the existing implementation is nonfunctional and cannot reasonably be repaired, contains serious security/data-loss risks, the task explicitly requests it, or the maintainer approves it after the need is documented.

If a rewrite seems necessary, document what is broken, why a minimal patch is insufficient, affected files, behavior to preserve, and migration or rollback path. Do not silently rewrite core systems.

## 5. Preservation Rule

Do not delete, rename, relocate, or archive files merely because they are ugly, unfamiliar, or inconsistent with personal preference. If removal or archival is genuinely necessary, explain why and obtain maintainer approval unless explicitly authorized.

## 6. Versioning Is Mandatory

Every meaningful change must bump the version according to `docs/VERSIONING.md`, unless the maintainer explicitly directs otherwise.

Inspect all actual version sources before changing one: `pyproject.toml`, `src/<package_name>/__init__.py`, `VERSION`, setup metadata, package constants, CLI output, installer/build metadata, and intentional documentation references. Do not blindly replace every matching number.

Semantic Versioning:
- PATCH: compatible bug fixes and maintenance.
- MINOR: backward-compatible functionality.
- MAJOR: incompatible public API or behavior changes.

## 7. Changelog Is Mandatory

Every version bump must append an entry to `CHANGELOG.md`. Use Keep a Changelog categories where applicable: Added, Changed, Deprecated, Removed, Fixed, Security. Add new entries at the top. Do not rewrite historical entries.

## 8. Documentation Must Stay Current

If a change affects behavior, usage, configuration, architecture, packaging, dependencies, or developer workflow, update the relevant documentation. Do not claim documentation is current without checking it against implementation.

## 9. Runtime and Interface Integrity

Every exposed command, public function, configuration option, endpoint, or user-facing control must have honest operational behavior. It must be implemented, explicitly disabled, intentionally hidden, or clearly documented as unsupported. Active dead placeholders are prohibited. Validate inputs and report errors clearly.

## 10. Testing and Validation

Run the most relevant available checks before finishing. Depending on the project:

```bash
ruff check .
ruff format --check .
pytest
python -m compileall src
python -m build
```

Do not run mutating commands unless authorized. Formatting commands can modify files; inspect scope and authorization first. If a check cannot run, state that clearly. Never claim tests or builds passed unless actually run.

## 11. Lint and Style Rules

Follow the repository's configured style and supported Python version. Preserve behavior while fixing lint issues. Avoid unrelated formatting churn.

## 12. Dependency Rules

Do not add dependencies casually. Verify necessity, maintenance, Python/platform compatibility, correct dependency group, and documentation impact. Do not replace a dependency or build backend solely because another option is preferred.

## 13. File and Naming Rules

Do not rename or move files unless necessary or explicitly requested. When authorized, update imports, tests, docs, packaging, and references.

## 14. Security and Safety Rules

Treat input, paths, environment variables, subprocess arguments, network responses, deserialization, and credentials as trust boundaries.

- Never commit secrets, tokens, private keys, or credentials.
- Avoid `shell=True`; justify it if unavoidable.
- Validate paths before destructive or privileged operations.
- Use safe APIs and parameterized operations.
- Do not execute untrusted serialized data or downloaded code.
- Avoid logging secrets or sensitive user data.
- Ask before destructive operations or security-boundary changes.

## 15. Git and Commit Hygiene

Keep changes focused and reviewable. Do not reset user work, discard uncommitted changes, rewrite history, force-push, rebase, amend commits, delete branches, or delete files unless explicitly requested. Never claim a Git operation succeeded without observing its result.

## 16. Final Response Requirements

At task completion, report what changed, files changed, version before/after, changelog/docs updates, checks actually run and results, known issues, and anything not verified. Do not hide failures or fabricate completion.

## 17. Task Execution Workflow

1. Read the request.
2. Identify the smallest safe scope.
3. Inspect relevant files and instructions.
4. Perform a read-only audit before modifications.
5. Check version sources and dependencies.
6. Implement only the authorized change.
7. Add/update tests where practical.
8. Update documentation.
9. Bump version and changelog when required.
10. Run relevant checks.
11. Inspect the final diff.
12. Report evidence and remaining uncertainty.

## 18. Read-Only Audit Before Modification

The initial audit must not modify files, install dependencies, alter configuration, create replacement files, commit changes, or otherwise mutate repository state. Establish relevant structure, implementation, instructions, configuration, version sources, tests, validation commands, Git state, dependencies, and interfaces. If a material ambiguity is discovered, stop and ask.

## 19. Evidence Over Assumption

Do not invent facts, APIs, dependency behavior, configuration, architecture, requirements, test results, command output, Git state, or successful execution.

Distinguish:
- **Confirmed:** directly observed.
- **Verified:** tested or independently checked.
- **Inferred:** logically derived but not directly confirmed.
- **Unknown:** insufficient evidence.
- **Blocked:** required information is unavailable.

Never present an inference as confirmed.

## 20. Ambiguity and Intent

Do not silently reinterpret ambiguous requests. If multiple interpretations materially change implementation, stop and ask. A request authorizes the work required for that task, not unrelated refactoring, redesign, deletion, dependency replacement, or architecture changes.

## 21. Consequential Decisions

Do not independently make materially consequential decisions not established by the user or project instructions, including major architecture changes, public API changes, persistent data migrations, removal of functionality, security-boundary changes, or destructive operations. Explain the blocker and obtain direction first.

## 22. Post-Change Verification

After editing: inspect the diff, check unintended changes, run relevant validation, verify requested behavior where practical, and report failures/unverified areas honestly.

## 23. Maintainer Preference

The maintainer values directness, minimal responsible changes, working software, preserved history, clear versioning, accurate changelogs, and documentation that matches reality. Treat the project like it matters.
