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


### Version-manager ownership

If a project is configured for and actively managed by Semantic Version Forge (svf), the project's semantic-version source and synchronization targets are owned by svf. Agents MUST NOT manually bump, synchronize, or otherwise alter those managed version values as part of unrelated repository changes. Version changes in an svf-managed project MUST be performed through svf and its configured synchronization workflow. Manual version bumps are permitted only for projects that are not being managed by svf, or when the maintainer explicitly authorizes an exception.

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


## Additional AI Agent Requirements: Packaging, Help, and User Documentation

Apply the Cross-Platform Packaging and User Documentation Contract below to this repository. For software products, this contract governs every supported distribution method. For templates and packaging-tool repositories, preserve the same requirements in generated project guidance and template output.



---

# Cross-Platform Packaging and User Documentation Contract

These requirements are additive. They supplement existing project-specific instructions and do not replace, weaken, or silently reinterpret them.

## 1. One product, one installation contract

Every supported distribution format for the same software MUST deliver an equivalent, complete product installation.

This requirement applies to every format the project supports, including as applicable:

- Python source distributions, wheels, and supported Python installers;
- Termux packages and Termux YAML manifests;
- Debian packages and APT repositories;
- Arch Linux packages and PKGBUILD-based builds;
- RPM packages;
- Alpine packages;
- AppImage and other portable Linux bundles;
- Windows installers and portable distributions;
- macOS application bundles, disk images, and installers;
- source builds and other project-supported installation paths.

A project is not required to support every format. The project MUST clearly identify which formats are supported, experimental, planned, or unsupported. However, once a format is declared supported, it MUST satisfy this contract.

The installation format is a delivery mechanism, not a separate product definition. Users MUST NOT receive materially different application capabilities, command interfaces, configuration behavior, or required resources merely because they selected a different package format.

## 2. Canonical release payload

Each product MUST define one canonical release payload or an equivalent machine-verifiable payload specification. Every supported packaging backend MUST derive its installed file set from that specification or from a demonstrably equivalent source of truth.

The specification MUST identify, as applicable:

- executable binaries and application entry points;
- Python modules, libraries, plugins, and runtime resources;
- GUI assets, icons, desktop entries, MIME definitions, and application metadata;
- default configuration files and configuration schema;
- templates, migrations, schemas, certificates, and other required data files;
- shell completion files and command aliases;
- man pages and other user manuals;
- usage examples and reference documentation;
- license, copyright, and third-party notices;
- changelog and release information;
- service definitions, integration files, and platform-specific support resources;
- uninstall metadata or other information required for safe removal.

Every packaging backend MUST install all files required for the software to function as documented. It MUST NOT omit a required resource merely because a packaging format or build script has a separate implementation.

Documentation may be installed in platform-appropriate locations, and platform-specific executable artifacts may differ. The logical documentation set and user-visible product capabilities MUST remain equivalent. A format-specific omission MUST be explicitly justified and documented.

## 3. Installation behavior parity

Every supported installer MUST implement the same product-level lifecycle contract:

- install the product and its required runtime resources;
- expose the documented commands, launchers, APIs, and interfaces;
- install or generate the same documented default configuration;
- preserve user configuration and user data during upgrades unless a documented migration explicitly requires otherwise;
- perform required configuration or data migrations safely and transparently;
- establish required permissions and platform integrations;
- report actionable errors when prerequisites or permissions are missing;
- support the documented upgrade and repair behavior;
- remove product-owned files during uninstall without deleting user data or unrelated files;
- provide an accurate installed-version and installation-location result where the platform supports it.

Package managers may own their native transaction, dependency, and uninstall mechanics. Product-specific scripts MUST NOT fight those mechanisms or perform surprising side effects.

Installing through a Python installer, Termux, APT/DEB, Arch, RPM, AppImage, Windows, macOS, or source installation MUST NOT result in different required application files, documentation, default behavior, command capabilities, or configuration semantics.

## 4. Platform-specific differences

Platform differences are allowed only when required by the operating system, runtime, package ecosystem, filesystem layout, security model, or user interaction conventions.

Examples include executable formats, filesystem destinations, service managers, desktop integration, permissions, signing, application bundle layout, dependency declarations, and platform-native launchers.

Every such difference MUST be:

1. identified in the packaging documentation;
2. limited to the platform-specific implementation detail;
3. tested or validated on the relevant platform when practical; and
4. prevented from changing the product-level contract without an explicit product decision.

Do not claim that two package formats are equivalent merely because both build successfully.

## 5. Packaging metadata, build scripts, and installers

All package metadata, manifests, build scripts, installer scripts, release workflows, and backend adapters MUST describe or produce the same canonical product payload.

Contributors and agents MUST inspect every supported packaging path when changing:

- application entry points or command names;
- modules, resources, plugins, assets, or runtime dependencies;
- default or user configuration;
- documentation or man pages;
- permissions, services, desktop integration, or filesystem paths;
- version metadata or release contents;
- installation, upgrade, repair, or uninstall behavior.

Do not independently add a file to one package format while omitting it from another supported format. Do not maintain conflicting versions of product metadata when a canonical source or generated manifest can be used.

Build scripts MUST distinguish building from installing. Building a package MUST NOT silently install it on the host, modify active system prefixes, publish a release, or perform unrelated destructive operations.

Generated metadata and package artifacts MUST be reproducible to the extent supported by the toolchain. Validation MUST distinguish metadata validation, mocked backend tests, native package builds, payload inspection, and actual installation tests. Passing one category MUST NOT be reported as proof of another.

## 6. Required packaging parity validation

For each supported format, maintain an auditable mapping between the canonical release payload and the package's installed filesystem contents.

Where practical, automate checks that compare:

- required paths and file presence;
- executable names and entry points;
- application version metadata;
- configuration defaults and schema;
- man pages and user documentation;
- icons, desktop entries, plugins, templates, and runtime data;
- dependency declarations and runtime requirements;
- uninstall ownership and preservation of user data.

A parity check MUST fail when a required payload item is missing from a supported package. Differences that are intentionally platform-specific MUST be enumerated as explicit exceptions rather than hidden through broad exclusions.

At least one clean installation test SHOULD be maintained for each supported package family and platform. Tests MUST verify actual installed behavior where feasible, not only inspect package metadata.

## 7. User manuals and man pages are required deliverables

Every user-facing software product MUST provide useful operating documentation appropriate to its interfaces. Documentation is part of the product, not an optional development extra.

For command-line applications, provide:

- a man page for the primary command;
- man pages for additional major commands when their interfaces warrant separate references;
- complete command and option reference documentation;
- examples of common and advanced workflows;
- help for applicable subcommands;
- installation, configuration, troubleshooting, and uninstall instructions.

For GUI applications, provide a user manual covering the interface, workflows, settings, dialogs, menus, shortcuts, supported file formats, error recovery, and relevant integration behavior.

For APIs, libraries, services, and automation tools, provide API or function references, configuration documentation, request/response or function examples, lifecycle information, and operational guidance appropriate to the actual public interface.

The manuals MUST be written for users and operators who did not develop the software. Use professional, neutral product documentation language. Do not address an individual maintainer, refer to private conversations, narrate how an AI agent wrote the code, or assume that the reader already knows the implementation.

Documentation MUST describe observed, implemented behavior. Clearly identify unsupported, experimental, optional, or platform-limited behavior.

## 8. Configuration documentation requirements

Every user-editable configuration file, environment variable, command-line setting, or remotely configurable option MUST be documented.

For each setting, document:

- exact key or option name;
- purpose and effect;
- data type;
- default value, or explicitly state that no default exists;
- accepted values, ranges, and format;
- whether the setting is required or optional;
- where the setting is read and how it is applied;
- precedence when multiple configuration sources exist;
- interactions or dependencies with other settings;
- validation rules and behavior for invalid values;
- a working example;
- whether a restart, reload, regeneration, or migration is required.

For structured configuration systems such as TOML, YAML, JSON, INI, or project-specific manifests, include a complete annotated example and explain every section and field. Do not document only the obvious settings while leaving nested or less common sections unexplained.

When configuration behavior is non-obvious, document the exact syntax and operational sequence. For example, a synchronization section must explain its supported targets, source and destination semantics, mapping rules, direction, conflict behavior, validation, and how a user can verify that synchronization occurred, but only to the extent those behaviors are confirmed by the implementation.

## 9. CLI and command help requirements

Every CLI MUST expose a discoverable general help interface, conventionally through `--help` and, where appropriate, `-h` or a `help` command.

Every command MUST communicate its purpose, syntax, arguments, options, defaults, accepted values, and relevant examples. Nested command systems MUST provide help for applicable subcommands, including a way to discover available subcommands without executing them.

Help output MUST:

- be accurate and generated from, or validated against, the actual command parser and implementation;
- include common usage examples;
- identify required and optional arguments;
- explain defaults and environment/configuration interactions;
- avoid exposing secrets or private implementation details;
- return useful output without performing the requested operation;
- use clear, user-facing language and actionable error messages.

If a command genuinely has no meaningful subcommands or no applicable secondary help surface, document why. Do not omit help merely for implementation convenience.

GUI applications and APIs MUST provide equivalent discoverability through their user manual, built-in help/about surfaces, API reference, or other appropriate interface documentation.

## 10. Documentation validation and release inclusion

Documentation must be checked as part of release validation.

For each supported package, verify that the applicable manuals, man pages, configuration references, examples, licenses, and notices are present in the installed payload and accessible at documented locations.

Man pages MUST use the correct section and platform installation conventions. Their source files MUST remain maintained alongside the implementation. Package build scripts MUST include them in the resulting artifact.

When a command, option, configuration key, API, UI action, installer, package format, or lifecycle behavior changes, update every affected user-facing reference in the same change set.

Do not leave examples, help output, or manuals describing removed or nonexistent behavior.

## 11. Contribution requirements for packaging changes

Any contribution that changes packaging, build metadata, release payloads, installers, installation paths, runtime dependencies, or uninstall behavior MUST:

1. inspect the canonical release payload specification;
2. inspect all supported package formats and their build/install scripts;
3. explain the intended behavior and any platform exceptions;
4. update all affected metadata and package definitions;
5. update user and maintainer documentation;
6. update or add payload parity and lifecycle tests where practical;
7. validate each affected package backend;
8. report which package formats were actually built and which were actually installed and tested.

A pull request MUST NOT be marked complete based solely on one successful package build when other supported formats may be affected.

## 12. AI agent enforcement

AI agents MUST treat this contract as a release requirement.

Before changing packaging, they MUST perform a read-only audit of all relevant package formats, metadata, build scripts, installer/uninstaller scripts, documentation payloads, and tests.

Agents MUST preserve existing files and behavior outside the explicit task scope. They MUST NOT delete, rewrite, reorganize, rename, or replace unrelated files or sections.

When a requested change cannot be applied consistently across supported formats, agents MUST identify the exact mismatch and either complete the consistent change or report the specific blocker. They MUST NOT silently update only the easiest backend.

Agents MUST NOT invent supported package formats, installation behavior, configuration semantics, commands, manual content, or validation results.

## Project-specific documentation standards

Before changing project behavior, packaging, interfaces, configuration, or release documentation, read [docs/PROJECT_STANDARDS.md](docs/PROJECT_STANDARDS.md) and keep it aligned with the actual implementation. These standards supplement this file and do not authorize unrelated changes.
