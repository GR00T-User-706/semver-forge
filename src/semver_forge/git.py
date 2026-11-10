"""Git subprocess wrapper. Commands are passed as argument arrays, never shell strings."""

import subprocess
from pathlib import Path

from .errors import GitError

name = "git"


def run(args, cwd=None, check=True, timeout=30):
    try:
        p = subprocess.run(
            ["git", *map(str, args)],
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise GitError(f"git command failed: {e}") from e
    if check and p.returncode:
        raise GitError(f"git {' '.join(map(str, args))} failed: {p.stderr.strip()}")
    return p


def available(path=None):
    """Return whether Git is installed and path belongs to a Git worktree."""
    try:
        p = run(["rev-parse", "--show-toplevel"], cwd=path, check=False)
    except GitError:
        return False
    return p.returncode == 0


def root(path=None):
    p = run(["rev-parse", "--show-toplevel"], cwd=path, check=False)
    if p.returncode:
        raise GitError("not inside a Git repository")
    return Path(p.stdout.strip()).resolve()


def is_dirty(path):
    return bool(run(["status", "--porcelain"], cwd=path).stdout.strip())


def branch(path):
    return (
        run(["symbolic-ref", "--quiet", "--short", "HEAD"], cwd=path, check=False).stdout.strip()
        or None
    )


def head(path):
    return run(["rev-parse", "HEAD"], cwd=path).stdout.strip()


def tags(path):
    return run(["tag", "--list"], cwd=path).stdout.splitlines()


def commits(path, since=None):
    args = ["log", "--format=%H%x1f%s%x1f%b%x1e"]
    if since:
        args.append(f"{since}..HEAD")
    else:
        args.append("HEAD")
    raw = run(args, cwd=path).stdout
    out = []
    for rec in raw.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        bits = rec.split("\x1f", 2)
        if len(bits) == 3:
            out.append(
                {
                    "hash": bits[0],
                    "subject": bits[1],
                    "body": bits[2],
                    "message": bits[1] + ("\n\n" + bits[2] if bits[2] else ""),
                }
            )
    return out


def history(path, since=None):
    """Return commit records for all commits in the selected history range."""
    args = ["log", "--format=%H%x1f%s%x1f%b%x1e"]
    if since:
        args.append(f"{since}..HEAD")
    raw = run(args, cwd=path).stdout
    out = []
    for rec in raw.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        bits = rec.split("\x1f", 2)
        if len(bits) == 3:
            out.append(
                {
                    "hash": bits[0],
                    "subject": bits[1],
                    "body": bits[2],
                    "message": bits[1] + ("\n\n" + bits[2] if bits[2] else ""),
                }
            )
    return out


def status_paths(path):
    """Return paths reported by Git status."""
    paths = []
    for line in run(["status", "--porcelain"], cwd=path).stdout.splitlines():
        if len(line) < 4:
            continue
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value)
    return paths


def diff_head(path):
    """Return the complete working-tree diff relative to HEAD."""
    return run(["diff", "HEAD", "--"], cwd=path, check=False).stdout


def staged_diff(path):
    """Return the currently staged diff."""
    return run(["diff", "--cached", "--"], cwd=path, check=False).stdout


def stage_all(path):
    run(["add", "-A"], cwd=path)


def commit(path, message):
    return run(["commit", "-m", message], cwd=path)


def tag_commit(path, tag):
    return run(["rev-list", "-n", "1", tag], cwd=path, check=False).stdout.strip() or None
