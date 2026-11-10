"""Intelligent Conventional Commit suggestions from the current worktree."""

from __future__ import annotations

from pathlib import Path

COMMIT_TYPES = (
    "feat",
    "fix",
    "perf",
    "refactor",
    "docs",
    "test",
    "build",
    "ci",
    "chore",
)


def _path_matches(paths, prefixes=(), suffixes=()):
    lowered = [path.lower() for path in paths]
    return bool(lowered) and all(
        any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)
        or any(path.endswith(suffix) for suffix in suffixes)
        for path in lowered
    )


def infer_type(paths: list[str], diff: str) -> tuple[str, str]:
    """Infer a Conventional Commit type and return (type, confidence)."""
    lowered = diff.lower()
    if _path_matches(paths, prefixes=("docs",), suffixes=(".md", ".rst", ".txt")):
        return "docs", "high"
    if _path_matches(
        paths,
        prefixes=("tests", "test"),
        suffixes=("_test.py", ".test.js", ".spec.js"),
    ):
        return "test", "high"
    if _path_matches(paths, prefixes=(".github",)):
        return "ci", "high"
    if paths and all(
        path.lower()
        in {"pyproject.toml", "setup.cfg", "setup.py", "package-lock.json", "cargo.lock"}
        or path.lower().startswith(("packaging/", "docker/", ".docker/", "build/"))
        for path in paths
    ):
        return "build", "medium"
    if any(
        word in lowered
        for word in ("performance", "perf", "latency", "throughput", "optimiz", "benchmark")
    ):
        return "perf", "medium"
    if any(
        word in lowered
        for word in (
            "bug",
            "fix",
            "fixed",
            "fixes",
            "regression",
            "correct",
            "incorrect",
            "broken",
            "error handling",
            "exception handling",
        )
    ):
        return "fix", "medium"
    if any(
        word in lowered
        for word in (
            "add ",
            "added ",
            "adds ",
            "new ",
            "feature",
            "implement",
            "introduced",
            "support for",
        )
    ):
        return "feat", "medium"
    if any(
        word in lowered
        for word in ("refactor", "restructure", "rename", "reorganize", "extract", "simplify")
    ):
        return "refactor", "medium"
    return "refactor", "low"


def infer_scope(paths: list[str]) -> str | None:
    """Infer a stable scope from changed paths."""
    clean = [path.replace("\\", "/") for path in paths if path]
    if not clean:
        return None
    if len(clean) == 1:
        parts = Path(clean[0]).parts
        name = Path(parts[-1]).stem
        if name in {"__init__", "__main__"} and len(parts) > 1:
            return parts[-2].replace("_", "-")
        return name.replace("_", "-")
    common = Path(clean[0])
    for path in clean[1:]:
        other = Path(path)
        shared = []
        for left, right in zip(common.parts, other.parts, strict=False):
            if left != right:
                break
            shared.append(left)
        if not shared:
            return None
        common = Path(*shared)
    value = common.name
    return None if value in {"src", "tests", "test", "."} else value.replace("_", "-")


def generate_summary(commit_type: str, scope: str | None) -> str:
    target = scope or "project"
    return {
        "feat": f"add {target} support",
        "fix": f"fix {target} behavior",
        "perf": f"improve {target} performance",
        "refactor": f"refactor {target}",
        "docs": "update documentation",
        "test": "update tests",
        "build": "update build configuration",
        "ci": "update CI configuration",
        "chore": f"update {target}",
    }.get(commit_type, f"update {target}")


def format_message(
    commit_type: str, scope: str | None, summary: str, breaking: bool = False
) -> str:
    scope_text = f"({scope})" if scope else ""
    bang = "!" if breaking else ""
    return f"{commit_type}{scope_text}{bang}: {summary.strip()}"
