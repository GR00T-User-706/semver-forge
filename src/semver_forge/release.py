"""Local release orchestration. Remote publishing is intentionally not implemented by default."""

from pathlib import Path

from . import git
from .build import run_commands
from .changelog import release_notes, update_changelog
from .conventional_commits import classify
from .errors import BuildFailure, ReleaseFailure
from .locking import lock
from .safety import check_release_state
from .semver import Version
from .synchronization import sync
from .vcs import backend_for


def latest_release(root, cfg):
    backend = backend_for(root)
    prefix = cfg["git"].get("tag_prefix", "v")
    found = []
    for tag in backend.tags(root):
        value = tag[len(prefix) :] if prefix and tag.startswith(prefix) else tag
        try:
            v = Version.parse(value)
        except ValueError:
            continue
        found.append((v, tag))
    if not found:
        return None, None
    found.sort(key=lambda x: x[0].precedence_key())
    # Ambiguous tags at the same precedence but distinct names are unsafe.
    top = found[-1][0]
    names = [tag for v, tag in found if v.compare(top) == 0]
    if len(names) > 1:
        raise ReleaseFailure(f"ambiguous tags for version {top}: {', '.join(names)}")
    tag = names[0]
    return top, tag


def plan(root, cfg, override=None, prerelease=None):
    current = Version.parse(
        __import__("semver_forge.version_sources", fromlist=["read_version"]).read_version(
            root, cfg["version"]["source"]
        )
    )
    previous, tag = latest_release(root, cfg)
    baseline = cfg["git"].get("baseline") or tag
    commits = backend_for(root).commits(root, baseline)
    rules = dict(cfg.get("commits", {}))
    rules["unknown"] = cfg["git"].get("unknown_commit", rules.get("unknown", "ignore"))
    impacts = [classify(c["message"], rules) for c in commits]
    rank = {"patch": 1, "minor": 2, "major": 3}
    impact = max((x for x in impacts if x in rank), key=lambda x: rank[x], default=None)
    if override in rank:
        nextv = current.bump(override)
    elif override:
        nextv = Version.parse(override)
        if nextv.compare(current) <= 0:
            raise ReleaseFailure(
                f"explicit release version {nextv} must be greater than current version {current}"
            )
    elif prerelease:
        base = current.bump(impact or "patch") if not current.prerelease else current
        nextv = base.prerelease_next(prerelease)
    elif impact:
        nextv = current.bump(impact)
    else:
        nextv = current
    return {
        "current": current,
        "previous": previous,
        "tag": tag,
        "commits": commits,
        "impact": impact,
        "next": nextv,
        "rules": rules,
    }


def release(
    root,
    cfg,
    override=None,
    prerelease=None,
    dry_run=False,
    notes_only=False,
    yes=False,
    run_build=False,
):
    check_release_state(root, cfg, allow_dirty=False)
    lock_path = Path(root) / ".git" / "semver-forge.lock"
    with lock(lock_path):
        backend = backend_for(root)
        p = plan(root, cfg, override, prerelease)
        version = str(p["next"])
        prefix = cfg["git"].get("tag_prefix", "v")
        tag = prefix + version
        if tag in backend.tags(root):
            raise ReleaseFailure(f"tag already exists: {tag}; refusing to move or overwrite it")
        notes = release_notes(p["commits"], p["rules"])
        result = {
            "current": str(p["current"]),
            "next": version,
            "impact": p["impact"],
            "previous_tag": p["tag"],
            "commit_count": len(p["commits"]),
            "tag": tag,
            "dry_run": dry_run,
            "notes": notes,
        }
        if notes_only or dry_run:
            return result
        if (
            p["impact"] is None
            and not override
            and not prerelease
            and not cfg["release"].get("release_when_no_changes", False)
        ):
            raise ReleaseFailure(
                "no release-relevant commits; use an explicit bump or configure "
                "release_when_no_changes"
            )
        if cfg["release"].get("require_confirmation", True) and not yes:
            try:
                answer = (
                    input(f"Create local release {tag} and modify project files? [y/N] ")
                    .strip()
                    .lower()
                )
            except EOFError:
                answer = ""
            if answer not in ("y", "yes"):
                raise ReleaseFailure(
                    "release cancelled; rerun with --yes to authorize without an interactive prompt"
                )
        tests = run_commands(cfg["release"].get("test_commands", []), root, "test")
        if run_build and not cfg["release"].get("build_commands", []):
            raise BuildFailure("build requested but no build_commands are configured")
        builds = (
            run_commands(cfg["release"].get("build_commands", []), root, "build")
            if run_build
            else {
                "status": "not_requested",
                "configured": bool(cfg["release"].get("build_commands")),
            }
        )
        sync_result = sync(root, cfg, version)
        notes_file = cfg["release"].get("notes_file")
        if notes_file:
            update_changelog(Path(root) / notes_file, version, notes)
        if cfg["release"].get("commit_version", True):
            files = [x["file"] for x in sync_result if x["changed"]]
            if notes_file:
                files.append(str(Path(root) / notes_file))
            if files:
                git.run(
                    [
                        "add",
                        "--",
                        *[
                            str(Path(f).relative_to(root)) if Path(f).is_absolute() else f
                            for f in files
                        ],
                    ],
                    cwd=root,
                )
                git.run(["commit", "-m", f"chore(release): {version}"], cwd=root)
        tag_args = (
            ["tag", "-a", tag, "-m", f"Release {version}"]
            if cfg["release"].get("annotated_tag", True)
            else ["tag", tag]
        )
        git.run(tag_args, cwd=root)
        if backend.tag_commit(root, tag) != backend.head(root):
            raise ReleaseFailure(f"tag verification failed: {tag} does not point to HEAD")
        artifacts = []
        for pattern in cfg["release"].get("artifact_paths", []):
            artifacts.extend(str(x) for x in Path(root).glob(pattern))
        result.update(
            {
                "status": "created_locally",
                "tests": tests,
                "build": builds,
                "synchronization": sync_result,
                "artifacts": artifacts,
                "published": False,
                "head": backend.head(root),
            }
        )
        return result
