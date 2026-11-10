from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from . import __version__, git
from .changelog import release_notes, update_changelog
from .check import inspect_project
from .commit import COMMIT_TYPES, format_message, generate_summary, infer_scope, infer_type
from .config import find_config
from .config_scopes import (
    config_edit,
    config_get,
    config_report,
    config_write,
    effective_config,
    scope_paths,
)
from .discovery import discover
from .errors import ConfigError, ForgeError
from .metadata_discovery import discover_sync_targets
from .operation_log import record
from .release import plan, resolve_changelog_path
from .semver import Version
from .synchronization import sync
from .version_sources import read_version


def parser():
    """Build the deliberately small public CLI."""
    p = argparse.ArgumentParser(
        prog="svf",
        description=(
            "Initialize version tracking, calculate and apply the next version, "
            "or synchronize metadata."
        ),
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--project", help="project path (default: current directory)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--verbose", action="store_true", help="show expanded operation details")
    p.add_argument("--debug", action="store_true", help="show diagnostic details and tracebacks")
    sub = p.add_subparsers(dest="cmd", required=True)

    init_cmd = sub.add_parser(
        "init",
        help="initialize SemVer Forge tracking in this project",
        description=(
            "Inspect existing version metadata and create the project configuration. "
            "Conflicting version sources must be resolved before initialization."
        ),
        epilog="Example: svf init --yes",
    )
    init_cmd.add_argument(
        "--yes",
        action="store_true",
        help="authorize replacing existing configuration",
    )

    next_cmd = sub.add_parser(
        "next",
        help="inspect Git history, choose the next version, and update configured version files",
        description=(
            "Classify commits since the saved Git boundary and apply the highest configured "
            "Semantic Versioning impact. By default, show the proposed changes and ask for "
            "authorization before writing. Use --yes to authorize without prompting."
        ),
        epilog="Examples: svf next; svf next --yes --explain",
    )
    next_cmd.add_argument(
        "--yes",
        action="store_true",
        help="authorize all proposed writes without prompting",
    )
    next_cmd.add_argument(
        "--explain",
        action="store_true",
        help="include why the version was or was not changed",
    )

    changelog_cmd = sub.add_parser(
        "changelog",
        help="compare Git history with CHANGELOG.md and append missing entries",
    )
    changelog_cmd.add_argument("--yes", action="store_true", help="apply changes without prompting")

    commit_cmd = sub.add_parser(
        "commit",
        help="intelligently create a Conventional Commit from current changes",
    )
    commit_cmd.add_argument(
        "--type", choices=COMMIT_TYPES, help="override the inferred commit type"
    )
    commit_cmd.add_argument("--scope", help="override the inferred commit scope")
    commit_cmd.add_argument("--message", help="use this complete commit message")
    commit_cmd.add_argument(
        "--breaking", action="store_true", help="mark the generated commit as breaking"
    )
    commit_cmd.add_argument(
        "--all", action="store_true", help="stage all current changes before committing"
    )
    commit_cmd.add_argument(
        "--yes", action="store_true", help="accept inferred values and stage all changes"
    )

    sync_cmd = sub.add_parser(
        "sync",
        help="synchronize configured metadata to the canonical version",
        description=(
            "Copy the canonical version into configured metadata fields. "
            "--discover registers additional supported version fields before synchronization."
        ),
        epilog="Examples: svf sync; svf sync --discover; svf sync --yes",
    )
    sync_cmd.add_argument(
        "--yes",
        action="store_true",
        help="authorize all proposed writes without prompting",
    )
    sync_cmd.add_argument(
        "--discover",
        action="store_true",
        help="recursively discover supported version metadata before synchronizing",
    )
    sync_cmd.add_argument(
        "--key",
        dest="discover_keys",
        action="append",
        metavar="KEY",
        help="custom version key to search for during --discover; may be repeated",
    )
    sync_cmd.add_argument(
        "--version",
        metavar="VERSION",
        help="use this target version instead of the canonical version",
    )
    config_cmd = sub.add_parser(
        "config",
        help="view and manage system, user, and project configuration",
        description=(
            "Print the selected TOML configuration by default. Use --list for grouped settings, "
            "get/set/unset to manage individual values, and --verbose for merged scope details."
        ),
        epilog="Example: svf config set commits.types.feat '\"minor\"'",
    )
    config_cmd.add_argument(
        "--global", dest="scope_global", action="store_true", help="select ~/.svfconfig"
    )
    config_cmd.add_argument(
        "--system", dest="scope_system", action="store_true", help="select the system svfconfig"
    )
    config_cmd.add_argument(
        "--edit", action="store_true", help="open the selected scope in VISUAL or EDITOR"
    )
    config_cmd.add_argument(
        "--list", action="store_true", help="list configuration settings grouped by TOML table"
    )
    config_cmd.add_argument(
        "--get", dest="get_key", metavar="KEY", help="read one effective setting"
    )
    config_cmd.add_argument(
        "--set",
        dest="set_pair",
        nargs=2,
        metavar=("KEY", "TOML_VALUE"),
        help="set a setting",
    )
    config_cmd.add_argument(
        "--unset",
        dest="unset_key",
        metavar="KEY",
        help="remove a setting from the selected scope",
    )
    config_cmd.add_argument("action", nargs="?", choices=("get", "set", "unset"))
    config_cmd.add_argument("key", nargs="?")
    config_cmd.add_argument("value", nargs="?")

    sub.add_parser(
        "check",
        help="read-only project, version, and configuration diagnostics",
        description=(
            "Show the project name, canonical version, and synchronized files. "
            "Use --verbose for the full inspection report or --debug for diagnostics."
        ),
        epilog="This command is read-only and never changes project files.",
    )
    config_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="show merged configuration scope details",
    )
    config_cmd.add_argument(
        "--debug",
        action="store_true",
        help="show configuration diagnostics and tracebacks",
    )
    return p


def _authorization_required(root):
    cfg, _paths, _unknown = effective_config(root)
    return cfg.get("authorization", {}).get("require_confirmation", True)


def _authorize_write(args, description, root=None):
    """Require explicit authorization unless --yes or config disables confirmation."""
    if args.yes:
        return
    root = root or Path(args.project or ".").expanduser().resolve()
    if not _authorization_required(root):
        return
    print(description)
    try:
        answer = input("Authorize these writes? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    if answer not in ("y", "yes"):
        raise ConfigError("operation cancelled")


def _format_output(data, indent=0):
    """Format nested result data as readable, indentation-based text."""
    prefix = " " * indent
    if isinstance(data, dict):
        if not data:
            return "{}"
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)) and value:
                lines.append(f"{prefix}{key}:")
                lines.append(_format_output(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_output(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return "[]"
        lines = []
        for item in data:
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{prefix}-")
                lines.append(_format_output(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_format_output(item)}")
        return "\n".join(lines)
    if data is None:
        return "null"
    return str(data)


def output(data, as_json=False):
    if as_json:
        rendered = json.dumps(data, indent=2, sort_keys=True, default=str)
    elif isinstance(data, str):
        rendered = data
    else:
        rendered = _format_output(data)
    if isinstance(data, str) and not as_json:
        sys.stdout.write(rendered if rendered.endswith("\n") else rendered + "\n")
    else:
        print(rendered)


def _format_config_list():
    """Render configuration settings by TOML table with descriptions and defaults."""
    sections = [
        (
            "project",
            [
                (
                    "name",
                    "string",
                    "unset",
                    "Optional project name used in reports.",
                ),
                (
                    "description",
                    "string",
                    '""',
                    "Optional project description.",
                ),
            ],
        ),
        (
            "version",
            [
                (
                    "initial",
                    "string",
                    '"0.1.0"',
                    "Starting version; must be valid Semantic Versioning.",
                ),
                (
                    "source",
                    "inline table",
                    '{ type = "text", file = "VERSION" }',
                    "Canonical version source definition; its fields are listed below.",
                ),
                (
                    "  type",
                    "string",
                    '"text"',
                    "Adapter: text, json, toml, yaml, shell, debian, or debian-changelog.",
                ),
                (
                    "  file",
                    "string",
                    '"VERSION"',
                    "Path to the canonical version file, relative to the project root.",
                ),
                (
                    "  key",
                    "string",
                    "optional",
                    "Dotted data key or shell variable; shell defaults to VERSION.",
                ),
            ],
        ),
        (
            "git",
            [
                (
                    "tag_prefix",
                    "string",
                    '"v"',
                    "Prefix removed from Git tags before parsing their version.",
                ),
                (
                    "require_clean",
                    "boolean",
                    "true",
                    "Legacy release safety setting; next and sync do not enforce it.",
                ),
                (
                    "baseline",
                    "string",
                    "unset",
                    "Optional commit or tag used as the history boundary.",
                ),
                (
                    "unknown_commit",
                    "string",
                    '"ignore"',
                    "Policy for unrecognized commits: ignore, major, minor, or patch.",
                ),
                (
                    "merge_commits",
                    "string",
                    '"ignore"',
                    "Reserved; current Git history traversal does not apply this policy.",
                ),
            ],
        ),
        (
            "commits",
            [
                (
                    "breaking_changes",
                    "boolean",
                    "true",
                    "Treat Conventional Commit breaking markers as a major impact.",
                ),
                (
                    "ignored_types",
                    "array of strings",
                    '["docs", "style", "refactor", "test", "build", "ci", "chore"]',
                    "Commit types excluded from version impact classification.",
                ),
                (
                    "unknown",
                    "string",
                    '"ignore"',
                    "Legacy fallback; git.unknown_commit currently takes precedence.",
                ),
            ],
        ),
        (
            "commits.types",
            [
                ("feat", "string", '"minor"', "Impact assigned to feat commits."),
                ("fix", "string", '"patch"', "Impact assigned to fix commits."),
                ("perf", "string", '"patch"', "Impact assigned to perf commits."),
                ("revert", "string", '"patch"', "Impact assigned to revert commits."),
                (
                    "additional types",
                    "string",
                    "major | minor | patch",
                    "Additional Conventional Commit types may be mapped to an impact.",
                ),
            ],
        ),
        (
            "authorization",
            [
                (
                    "require_confirmation",
                    "boolean",
                    "true",
                    "Require interactive authorization before mutating writes.",
                ),
            ],
        ),
        (
            "sync",
            [
                (
                    "targets",
                    "array of tables",
                    "[]",
                    "Version targets; each item requires type and file, with optional key.",
                ),
                (
                    "discovery_keys",
                    "array of strings",
                    "[]",
                    "Custom assignment keys searched by sync --discover.",
                ),
            ],
        ),
        (
            "release",
            [
                (
                    "commit_version",
                    "boolean",
                    "true",
                    "Legacy release setting; no effect while release execution is disabled.",
                ),
                (
                    "annotated_tag",
                    "boolean",
                    "true",
                    "Legacy release setting; no effect while release execution is disabled.",
                ),
                (
                    "notes_file",
                    "string",
                    '"CHANGELOG.md"',
                    "Legacy release setting; no effect while release execution is disabled.",
                ),
                (
                    "require_confirmation",
                    "boolean",
                    "true",
                    "Legacy release setting; no effect while release execution is disabled.",
                ),
                (
                    "release_when_no_changes",
                    "boolean",
                    "false",
                    "Legacy release setting; no effect while release execution is disabled.",
                ),
            ],
        ),
    ]
    lines = [
        "Recognized configuration settings",
        "Entries are TOML keys grouped by their table. Defaults are shown where applicable.",
        "Use dotted paths with config get/set/unset; use TOML table syntax when editing files.",
    ]
    for table, entries in sections:
        lines.extend(["", f"[{table}]"])
        for key, value_type, default, description in entries:
            lines.append(f"  {key:<22} {value_type:<17} default: {default}")
            lines.append(f"    {description}")
    lines.extend(
        [
            "",
            "Version source and sync target types: text, json, toml, yaml, shell, "
            "debian, debian-changelog.",
            "See svf-config(5) for TOML syntax, complete configuration details, and examples.",
        ]
    )
    return "\n".join(lines)


def _check_summary(report):
    project = report.get("project", {}).get("name") or "unknown"
    version = report.get("canonical", {}).get("version") or "unavailable"
    files = []
    for item in report.get("synchronization", []):
        filename = item.get("file")
        if filename and filename not in files:
            files.append(filename)
    lines = [f"Project: {project}", f"Version: {version}", "", "Synchronized files"]
    lines.extend(files)
    return "\n".join(lines)


def _config_text(root, scope):
    path = scope_paths(root)[scope]
    if not path.is_file():
        raise ConfigError(f"configuration file not found: {path}")
    return path.read_text(encoding="utf-8")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        parser().print_help()
        return 0
    # Accept global project/JSON options both before and after subcommands.
    moved = []
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] in {"--json", "--verbose", "--debug"}:
            moved.append(argv[i])
            i += 1
        elif argv[i] == "--project" and i + 1 < len(argv):
            moved.extend(argv[i : i + 2])
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    args = parser().parse_args(moved + rest)

    try:
        if args.cmd == "init":
            project = Path(args.project or ".").expanduser().resolve()
            if not project.is_dir():
                raise ConfigError(f"project directory does not exist: {project}")
            root = git.root(project) if git.available(project) else project
            path = find_config(root) or root / ".semver-forge.toml"
            # Discover and validate the project before asking permission to overwrite
            # configuration. A rejected initialization must never prompt for a write
            # that cannot safely happen.
            result = discover(root)
            if result["version_status"] == "conflict":
                details = "; ".join(
                    f"{item['source']['file']}={item['version']}"
                    for item in result["version_conflicts"]
                )
                raise ConfigError(
                    "conflicting existing version sources; resolve them before initialization: "
                    + details
                )
            if path.exists() and not args.yes:
                try:
                    answer = (
                        input(f"Overwrite existing configuration {path}? [y/N] ").strip().lower()
                    )
                except EOFError:
                    answer = ""
                if answer not in ("y", "yes"):
                    raise ConfigError(
                        f"initialization cancelled; existing configuration preserved: {path}"
                    )
            config_text = __import__(
                "semver_forge.discovery", fromlist=["render_config"]
            ).render_config(result)
            # Starting tracking establishes the history boundary. Older project
            # commits must not trigger a version bump on the first next invocation.
            if not path.exists() and git.available(root):
                head_result = git.run(["rev-parse", "--verify", "HEAD"], cwd=root, check=False)
                if head_result.returncode == 0:

                    def add_baseline(match):
                        return match.group(1) + f'\nbaseline = "{head_result.stdout.strip()}"'

                    config_text = re.sub(
                        r"(?m)^(tag_prefix\s*=.*)$",
                        add_baseline,
                        config_text,
                        count=1,
                    )
            # Validate the generated TOML and its schema before writing anything.
            try:
                import tomllib
            except ModuleNotFoundError:  # Python 3.10
                import tomli as tomllib
            try:
                tomllib.loads(config_text)
            except tomllib.TOMLDecodeError as exc:
                raise ConfigError(
                    f"internal error: generated configuration is invalid TOML: {exc}"
                ) from exc
            version_source = result["version"]["source"]
            version_path = root / version_source["file"]
            generated = {path: config_text}
            if result["version_status"] == "no_existing_version_source":
                if version_path.exists():
                    raise ConfigError(
                        "version destination already exists but could not be recognized: "
                        f"{version_path}"
                    )
                generated[version_path] = result["version"]["initial"] + "\n"
            _authorize_write(
                args,
                "SVF will create/update: " + ", ".join(str(target) for target in generated),
                root,
            )
            written = []
            try:
                for target, contents in generated.items():
                    fd, tmp = tempfile.mkstemp(prefix=".semver-forge-init-", dir=target.parent)
                    try:
                        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                            stream.write(contents)
                            stream.flush()
                            os.fsync(stream.fileno())
                        os.replace(tmp, target)
                        written.append(target)
                    finally:
                        if os.path.exists(tmp):
                            os.unlink(tmp)
            except Exception as exc:
                record("ERROR", "init.generate", "failed", error=exc)
                print(
                    "Initialization failed. Inspect generated files: "
                    f"{', '.join(map(str, written))}",
                    file=sys.stderr,
                )
                raise
            committed = False
            pushed = False
            stage_failed = False
            staged_files = []
            vcs_note = "no supported VCS detected; files created without a VCS commit"
            if git.available(root):
                rel = [str(p.relative_to(root)) for p in generated]
                try:
                    git.run(["add", "--", *rel], cwd=root)
                    staged_files = git.run(
                        ["diff", "--cached", "--name-only", "--", *rel], cwd=root, check=False
                    ).stdout.splitlines()
                except ForgeError as stage_exc:
                    stage_failed = True
                    record("ERROR", "init.stage", "failed", error=stage_exc)
                    staged_files = git.run(
                        ["diff", "--cached", "--name-only", "--", *rel], cwd=root, check=False
                    ).stdout.splitlines()
                    staged_list = ", ".join(staged_files) or "none"
                    vcs_note = (
                        f"staging failed: {stage_exc}; only these generated paths "
                        f"are staged: {staged_list}"
                    )
                if not stage_failed:

                    def push_configured_remote():
                        nonlocal pushed
                        try:
                            remotes = git.run(["remote"], cwd=root, check=False).stdout.split()
                        except ForgeError as push_exc:
                            return (
                                f"; remote push could not be checked: {push_exc}; "
                                "local commit preserved"
                            )
                        if not remotes:
                            return "; no Git remote configured"
                        try:
                            push = git.run(["push"], cwd=root, check=False)
                            pushed = push.returncode == 0
                            return "; remote push " + (
                                "succeeded" if pushed else "failed; local commit preserved"
                            )
                        except ForgeError as push_exc:
                            return f"; remote push failed: {push_exc}; local commit preserved"

                    try:
                        git.run(
                            [
                                "commit",
                                "--only",
                                "-m",
                                "chore(init): initialize SemVer Forge project configuration",
                                "--",
                                *rel,
                            ],
                            cwd=root,
                        )
                        committed = True
                        vcs_note = (
                            "generated files committed; unrelated staged changes "
                            "were left untouched"
                        )
                        vcs_note += push_configured_remote()
                        staged_files = []
                    except ForgeError as exc:
                        record("ERROR", "init.commit", "failed", error=exc)
                        try:
                            answer = (
                                input(
                                    "Commit failed ("
                                    f"{exc}). Correct the issue and retry the generated-files "
                                    "commit now? [y/N] "
                                )
                                .strip()
                                .lower()
                            )
                        except EOFError:
                            answer = ""
                        if answer in ("y", "yes"):
                            try:
                                git.run(
                                    [
                                        "commit",
                                        "--only",
                                        "-m",
                                        "chore(init): initialize SemVer Forge "
                                        "project configuration",
                                        "--",
                                        *rel,
                                    ],
                                    cwd=root,
                                )
                                committed = True
                                vcs_note = "generated files committed after retry"
                                vcs_note += push_configured_remote()
                                staged_files = []
                            except ForgeError as retry_exc:
                                record("ERROR", "init.commit.retry", "failed", error=retry_exc)
                                staged_list = ", ".join(staged_files) or "none"
                                vcs_note = (
                                    f"retry failed: {retry_exc}; generated files "
                                    f"remain staged: {staged_list}"
                                )
                        else:
                            staged_list = ", ".join(staged_files) or "none"
                            vcs_note = "commit not retried; generated files remain staged"
                            vcs_note += f": {staged_list}"
            record("INFO", "init", "completed")
            output(
                {
                    "initialized": str(path),
                    "version": result["version"]["initial"],
                    "version_source": result["version"]["source"],
                    "generated_files": [str(p) for p in generated],
                    "discovery": result["evidence"],
                    "inferred": {
                        "project": result["project"],
                        "sync_targets": result["sync_targets"],
                        "notes_file": result["notes_file"],
                    },
                    "committed": committed,
                    "pushed": pushed,
                    "staged_files": staged_files,
                    "vcs": vcs_note,
                },
                args.json,
            )
            return 2 if stage_failed else 0
        project = Path(args.project or ".").expanduser().resolve()
        if args.cmd in {"config", "check"}:
            root = git.root(project) if git.available(project) else project
        else:
            root = git.root(project)
        if args.cmd == "config":
            if args.scope_global and args.scope_system:
                raise ConfigError("choose only one configuration scope")
            scope = "system" if args.scope_system else "global" if args.scope_global else "project"
            read_scope = scope if args.scope_global or args.scope_system else None
            selected = sum(bool(item) for item in (args.get_key, args.set_pair, args.unset_key))
            if selected > 1 or (args.list and (selected or args.action or args.key or args.value)):
                raise ConfigError("choose only one config operation")
            if args.edit:
                if args.action or args.key or args.value or args.list or selected:
                    raise ConfigError("--edit cannot be combined with get, set, unset, or --list")
                output(config_edit(root, scope), args.json)
                return 0
            if args.get_key:
                output(config_get(root, args.get_key, read_scope), args.json)
                return 0
            if args.set_pair:
                output(config_write(root, scope, args.set_pair[0], args.set_pair[1]), args.json)
                return 0
            if args.unset_key:
                output(config_write(root, scope, args.unset_key, None, unset=True), args.json)
                return 0
            if args.action == "get":
                if not args.key or args.value is not None:
                    raise ConfigError("usage: svf config [--global|--system] get KEY")
                output(
                    config_get(root, args.key, read_scope),
                    args.json,
                )
                return 0
            if args.action == "set":
                if not args.key or args.value is None:
                    raise ConfigError("usage: svf config [--global|--system] set KEY TOML_VALUE")
                output(
                    config_write(root, scope, args.key, args.value),
                    args.json,
                )
                return 0
            if args.action == "unset":
                if not args.key or args.value is not None:
                    raise ConfigError("usage: svf config [--global|--system] unset KEY")
                output(config_write(root, scope, args.key, None, unset=True), args.json)
                return 0
            if args.action or args.key or args.value:
                raise ConfigError(
                    "use config --get KEY, --set KEY TOML_VALUE, --unset KEY, or config --list"
                )
            if args.list:
                output(_format_config_list(), args.json)
            elif args.verbose or args.debug or args.json:
                output(config_report(root, read_scope), args.json)
            else:
                output(_config_text(root, scope))
            return 0
        if args.cmd == "check":
            report = inspect_project(root)
            if args.verbose or args.debug or args.json:
                output(report, args.json)
            else:
                output(_check_summary(report))
            return 0
        config_path = find_config(root)
        if not config_path:
            raise ConfigError("no .semver-forge.toml found; run svf init")
        cfg, _paths, unknown = effective_config(root)
        if unknown:
            print("warning: unknown configuration keys: " + ", ".join(unknown), file=sys.stderr)
        current = Version.parse(read_version(root, cfg["version"]["source"]))

        if args.cmd == "changelog":
            from .changelog import sync_unreleased
            from .release import latest_release

            notes_file = cfg.get("release", {}).get("notes_file") or "CHANGELOG.md"
            notes_path = resolve_changelog_path(root, notes_file)
            _previous, tag = latest_release(root, cfg)
            commits = git.history(root, tag)
            preview = sync_unreleased(notes_path, commits, cfg.get("commits", {}), dry_run=True)

            if not preview["diverged"]:
                preview["status"] = "synchronized"
                preview["changed"] = False
                output(preview, args.json)
                return 0

            if _authorization_required(root) and not args.yes:
                try:
                    answer = (
                        input(
                            f"Update {notes_path} with {preview['missing_count']} missing commit "
                            "entries? [y/N] "
                        )
                        .strip()
                        .lower()
                    )
                except EOFError:
                    answer = ""
                if answer not in ("y", "yes"):
                    preview["status"] = "cancelled"
                    preview["changed"] = False
                    output(preview, args.json)
                    return 0

            result = sync_unreleased(notes_path, commits, cfg.get("commits", {}), dry_run=False)
            result["status"] = "updated"
            record("INFO", "changelog", "updated", missing=result["missing_count"])
            output(result, args.json)
            return 0

        if args.cmd == "commit":
            paths = git.status_paths(root)
            if not paths:
                raise ConfigError("working tree is clean; nothing to commit")

            diff = git.diff_head(root)
            inferred_type, confidence = infer_type(paths, diff)
            inferred_scope = infer_scope(paths)
            inferred_summary = generate_summary(inferred_type, inferred_scope)

            commit_type = args.type or inferred_type
            scope = args.scope if args.scope is not None else inferred_scope
            message = args.message

            if not message and not args.yes:
                print(f"Suggested type: {inferred_type} (confidence: {confidence})")
                print("Changed files:")
                for path in paths:
                    print(f"  {path}")
                choices = ", ".join(
                    f"{index + 1}={value}" for index, value in enumerate(COMMIT_TYPES)
                )
                selection = input(f"Commit type [{commit_type}] choices: {choices}: ").strip()
                if selection:
                    if selection.isdigit() and 1 <= int(selection) <= len(COMMIT_TYPES):
                        commit_type = COMMIT_TYPES[int(selection) - 1]
                    elif selection in COMMIT_TYPES:
                        commit_type = selection
                    else:
                        raise ConfigError(f"unknown commit type: {selection}")
                scope_value = input(f"Scope [{scope or 'none'}]: ").strip()
                if scope_value:
                    scope = scope_value
                summary = input(f"Summary [{inferred_summary}]: ").strip() or inferred_summary
                message = format_message(commit_type, scope, summary, breaking=args.breaking)
                print(f"Commit message: {message}")
                answer = input("Create this commit? [Y/n/e] ").strip().lower()
                if answer == "e":
                    edited = input("Commit message: ").strip()
                    if edited:
                        message = edited
                elif answer not in ("", "y", "yes"):
                    raise ConfigError("commit cancelled")

            if not message:
                message = format_message(
                    commit_type, scope, inferred_summary, breaking=args.breaking
                )

            if not args.yes and not args.all:
                answer = input("Stage all current changes for this commit? [Y/n] ").strip().lower()
                if answer not in ("", "y", "yes"):
                    raise ConfigError("commit cancelled")

            git.stage_all(root)
            if not git.staged_diff(root).strip():
                raise ConfigError("no changes are staged for commit")
            if _authorization_required(root) and not args.yes:
                answer = input(f"Authorize commit {message!r}? [y/N] ").strip().lower()
                if answer not in ("y", "yes"):
                    raise ConfigError("commit cancelled")
            git.commit(root, message)
            record("INFO", "commit", "completed")
            output(
                {
                    "type": commit_type,
                    "scope": scope,
                    "message": message,
                    "confidence": confidence,
                    "files": paths,
                    "committed": True,
                },
                args.json,
            )
            return 0

        if args.cmd == "next":
            proposed = plan(root, cfg)
            next_version = proposed["next"]
            changed = next_version.compare(current) > 0
            sync_result = []
            changelog_result = None
            notes_file = cfg.get("release", {}).get("notes_file", "CHANGELOG.md")
            changelog_path = resolve_changelog_path(root, notes_file)
            notes = release_notes(proposed["commits"], proposed["rules"]) if changed else []

            if changed:
                print(f"SVF will update the project version from {current} to {next_version}.")
                print(f"SVF will update configured version targets and {changelog_path}.")
            else:
                print(
                    f"SVF will record the current Git history boundary in {config_path}; "
                    f"the version remains {current}."
                )
            _authorize_write(
                args,
                "SVF will update the version, metadata, changelog, and Git boundary.",
                root,
            )

            if changed:
                sync_result = sync(root, cfg, str(next_version), dry_run=False)
                update_changelog(
                    changelog_path,
                    str(next_version),
                    notes,
                    dry_run=False,
                )
                changelog_result = {
                    "path": str(changelog_path),
                    "changed": True,
                    "authorized": args.yes,
                    "notes": notes,
                }

            # Remember the processed Git boundary so the same commits are not
            # counted again on the next invocation.
            head = git.head(root)
            config_text = config_path.read_text(encoding="utf-8")
            baseline_line = f'baseline = "{head}"'
            if re.search(r"(?m)^baseline\s*=", config_text):
                config_text = re.sub(
                    r"(?m)^baseline\s*=.*$",
                    lambda _match: baseline_line,
                    config_text,
                    count=1,
                )
            else:
                config_text = re.sub(
                    r"(?m)^(tag_prefix\s*=.*)$",
                    lambda match: match.group(1) + chr(10) + baseline_line,
                    config_text,
                    count=1,
                )
            fd, temp_path = tempfile.mkstemp(prefix=".semver-forge-", dir=root)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                    stream.write(config_text)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp_path, config_path)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

            data = {
                "current": str(current),
                "next": str(next_version),
                "impact": proposed["impact"],
                "commit_count": len(proposed["commits"]),
                "changed": changed,
                "authorized": args.yes,
                "synchronization": sync_result,
                "changelog": changelog_result,
            }
            if args.explain:
                data["reason"] = (
                    "highest classified commit impact since the previous version boundary"
                    if proposed["impact"]
                    else "no release-relevant commits; version remains unchanged"
                )
            record("INFO", "next", "completed")
            output(data, args.json)
        elif args.cmd == "sync":
            version = args.version or str(current)
            sync_cfg = cfg
            discovered = []
            config_changes = None
            if args.discover:
                configured_keys = cfg.get("sync", {}).get("discovery_keys", [])
                custom_keys = [*configured_keys, *(args.discover_keys or [])]
                discovered = discover_sync_targets(
                    root,
                    cfg["version"]["source"],
                    custom_keys=custom_keys,
                )
                configured = cfg.get("sync", {}).get("targets", [])
                merged = []
                seen = set()
                for target in [*configured, *discovered]:
                    identity = (target["file"], target["type"], target.get("key"))
                    if identity not in seen:
                        seen.add(identity)
                        merged.append(target)
                sync_cfg = dict(cfg)
                sync_cfg["sync"] = dict(cfg.get("sync", {}))
                sync_cfg["sync"]["targets"] = merged
                config_changes = {
                    "file": str(config_path),
                    "previous_targets": configured,
                    "proposed_targets": merged,
                    "changed": merged != configured,
                }

            print(f"SVF will synchronize metadata to version {version}.")
            if config_changes and config_changes["changed"]:
                print(
                    "SVF will update discovered synchronization targets in the project "
                    "configuration."
                )
                for target in discovered:
                    print(f"  {target}")
            _authorize_write(
                args,
                "SVF will synchronize metadata and update discovered synchronization targets in project configuration.",
                root,
            )

            if config_changes and config_changes["changed"]:
                config_write(root, "project", "sync.targets", config_changes["proposed_targets"])
            result = sync(root, sync_cfg, version, False)
            record("INFO", "sync", "completed")
            if args.discover:
                output(
                    {
                        "canonical_version": version,
                        "discovered_targets": discovered,
                        "configuration": config_changes,
                        "synchronization": result,
                        "authorized": args.yes,
                    },
                    args.json,
                )
            else:
                output(result, args.json)
        else:
            raise ConfigError(f"command not implemented: {args.cmd}")
        return 0
    except ForgeError as e:
        record("ERROR", getattr(args, "cmd", "cli"), "failed", error=e)
        print(f"error: {e}", file=sys.stderr)
        if "args" in locals() and args.debug:
            import traceback

            traceback.print_exc()
        return e.exit_code
    except (ValueError, OSError, KeyError, TypeError) as e:
        record("ERROR", getattr(args, "cmd", "cli"), "failed", error=e)
        print(f"error: {e}", file=sys.stderr)
        if "args" in locals() and args.debug:
            import traceback

            traceback.print_exc()
        return 2
