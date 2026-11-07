from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from . import __version__, git
from .commit import COMMIT_TYPES, format_message, generate_summary, infer_scope, infer_type
from .config import find_config, load
from .discovery import discover
from .errors import ConfigError, ForgeError
from .metadata_discovery import discover_sync_targets
from .operation_log import record
from .release import plan
from .semver import Version
from .synchronization import sync
from .version_sources import read_version


def parser():
    """Build the deliberately small public CLI."""
    p = argparse.ArgumentParser(
        prog="semver-forge",
        description=(
            "Initialize version tracking, calculate and apply the next version, "
            "or synchronize metadata."
        ),
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--project", help="project path (default: current directory)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    init_cmd = sub.add_parser("init", help="initialize SemVer Forge tracking in this project")
    init_cmd.add_argument(
        "--yes",
        action="store_true",
        help="authorize replacing existing configuration",
    )

    next_cmd = sub.add_parser(
        "next",
        help="inspect Git history, choose the next version, and update configured version files",
    )
    next_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="show the proposed change without writing",
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
    changelog_cmd.add_argument("--dry-run", action="store_true", help="show changes without writing")
    changelog_cmd.add_argument("--yes", action="store_true", help="apply changes without prompting")

    commit_cmd = sub.add_parser(
        "commit",
        help="intelligently create a Conventional Commit from current changes",
    )
    commit_cmd.add_argument("--type", choices=COMMIT_TYPES, help="override the inferred commit type")
    commit_cmd.add_argument("--scope", help="override the inferred commit scope")
    commit_cmd.add_argument("--message", help="use this complete commit message")
    commit_cmd.add_argument("--breaking", action="store_true", help="mark the generated commit as breaking")
    commit_cmd.add_argument("--all", action="store_true", help="stage all current changes before committing")
    commit_cmd.add_argument("--yes", action="store_true", help="accept inferred values and stage all changes")
    commit_cmd.add_argument("--dry-run", action="store_true", help="show the proposal without staging or committing")

    sync_cmd = sub.add_parser(
        "sync",
        help="synchronize configured metadata to the canonical version",
    )
    sync_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="show changes without writing",
    )
    sync_cmd.add_argument(
        "--discover",
        action="store_true",
        help="recursively discover supported version metadata before synchronizing",
    )
    sync_cmd.add_argument(
        "--version",
        metavar="VERSION",
        help="use this target version instead of the canonical version",
    )
    return p


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
    print(rendered)


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
        if argv[i] == "--json":
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
        root = git.root(args.project)
        config_path = find_config(root)
        if not config_path:
            raise ConfigError("no .semver-forge.toml found; run semver-forge init")
        cfg, unknown = load(config_path)
        if unknown:
            print("warning: unknown configuration keys: " + ", ".join(unknown), file=sys.stderr)
        current = Version.parse(read_version(root, cfg["version"]["source"]))

        if args.cmd == "changelog":
            from .changelog import sync_unreleased
            from .release import latest_release, resolve_changelog_path

            notes_file = cfg.get("release", {}).get("notes_file") or "CHANGELOG.md"
            notes_path = resolve_changelog_path(root, notes_file)
            _previous, tag = latest_release(root, cfg)
            commits = git.history(root, tag)
            preview = sync_unreleased(notes_path, commits, cfg.get("commits", {}), dry_run=True)

            if args.dry_run:
                preview["status"] = "would_update" if preview["diverged"] else "synchronized"
                output(preview, args.json)
                return 0

            if not preview["diverged"]:
                preview["status"] = "synchronized"
                preview["changed"] = False
                output(preview, args.json)
                return 0

            if not args.yes:
                try:
                    answer = input(
                        f"Update {notes_path} with {preview['missing_count']} missing commit entries? [y/N] "
                    ).strip().lower()
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

            if not message and not args.yes and not args.dry_run:
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
                message = format_message(commit_type, scope, inferred_summary, breaking=args.breaking)

            if args.dry_run:
                output(
                    {
                        "type": commit_type,
                        "scope": scope,
                        "message": message,
                        "confidence": confidence,
                        "files": paths,
                        "committed": False,
                        "dry_run": True,
                    },
                    args.json,
                )
                return 0

            if not args.yes and not args.all:
                answer = input("Stage all current changes for this commit? [Y/n] ").strip().lower()
                if answer not in ("", "y", "yes"):
                    raise ConfigError("commit cancelled")

            git.stage_all(root)
            if not git.staged_diff(root).strip():
                raise ConfigError("no changes are staged for commit")
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
                    "dry_run": False,
                },
                args.json,
            )
            return 0

        if args.cmd == "next":
            proposed = plan(root, cfg)
            next_version = proposed["next"]
            changed = next_version.compare(current) > 0
            sync_result = []
            if changed:
                sync_result = sync(root, cfg, str(next_version), dry_run=args.dry_run)
            if not args.dry_run:
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
                "would_change": changed,
                "changed": changed and not args.dry_run,
                "dry_run": args.dry_run,
                "synchronization": sync_result,
            }
            if args.explain:
                data["reason"] = (
                    "highest classified commit impact since the previous version boundary"
                    if proposed["impact"]
                    else "no release-relevant commits; version remains unchanged"
                )
            record("INFO", "next", "dry-run" if args.dry_run else "completed")
            output(data, args.json)
        elif args.cmd == "sync":
            version = args.version or str(current)
            sync_cfg = cfg
            discovered = []
            if args.discover:
                discovered = discover_sync_targets(root, cfg["version"]["source"])
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
            result = sync(root, sync_cfg, version, args.dry_run)
            record("INFO", "sync", "dry-run" if args.dry_run else "completed")
            if args.discover:
                output(
                    {
                        "canonical_version": version,
                        "discovered_targets": discovered,
                        "synchronization": result,
                        "dry_run": args.dry_run,
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
        return e.exit_code
    except (ValueError, OSError, KeyError, TypeError) as e:
        record("ERROR", getattr(args, "cmd", "cli"), "failed", error=e)
        print(f"error: {e}", file=sys.stderr)
        return 2
