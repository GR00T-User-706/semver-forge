from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from . import __version__, git
from .config import find_config, load
from .discovery import discover
from .errors import ConfigError, ForgeError
from .operation_log import record
from .release import plan
from .semver import Version
from .synchronization import sync
from .version_sources import read_version


def parser():
    """Build the deliberately small public CLI."""
    p = argparse.ArgumentParser(
        prog="semver-forge",
        description="Initialize version tracking, calculate and apply the next version, or sync metadata.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--project", help="project path (default: current directory)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    init_cmd = sub.add_parser("init", help="initialize SemVer Forge tracking in this project")
    init_cmd.add_argument("--yes", action="store_true", help="authorize replacing existing configuration")

    next_cmd = sub.add_parser(
        "next",
        help="inspect Git history, choose the next version, and update configured version files",
    )
    next_cmd.add_argument("--dry-run", action="store_true", help="show the proposed change without writing")
    next_cmd.add_argument("--explain", action="store_true", help="include why the version was or was not changed")

    sync_cmd = sub.add_parser("sync", help="synchronize configured metadata to the canonical version")
    sync_cmd.add_argument("--dry-run", action="store_true", help="show changes without writing")
    sync_cmd.add_argument("--version", metavar="VERSION", help="use this target version instead of the canonical version")
    return p

def output(data, as_json=False):
    print(
        json.dumps(data, indent=2, sort_keys=True, default=str)
        if as_json
        else (data if isinstance(data, str) else "\n".join(f"{k}: {v}" for k, v in data.items()))
    )


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
            path = root / ".semver-forge.toml"
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
                        "test_commands": result["test_commands"],
                        "build_commands": result["build_commands"],
                        "artifact_paths": result["artifact_paths"],
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

        if args.cmd == "next":
            proposed = plan(root, cfg)
            next_version = proposed["next"]
            changed = next_version.compare(current) > 0
            sync_result = []
            if changed and not args.dry_run:
                sync_result = sync(root, cfg, str(next_version))
            data = {
                "current": str(current),
                "next": str(next_version),
                "impact": proposed["impact"],
                "commit_count": len(proposed["commits"]),
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
            result = sync(root, cfg, version, args.dry_run)
            record("INFO", "sync", "dry-run" if args.dry_run else "completed")
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
