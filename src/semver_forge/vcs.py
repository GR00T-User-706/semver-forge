"""Version-control abstraction.

SemVer Forge currently ships a Git backend. Other VCS implementations can satisfy
this protocol without changing release-planning policy.
"""
from __future__ import annotations

from typing import Protocol, Any
from pathlib import Path


class VCSBackend(Protocol):
    name: str

    def root(self, path: str | Path | None = None) -> Path: ...
    def is_dirty(self, path: str | Path) -> bool: ...
    def branch(self, path: str | Path) -> str | None: ...
    def head(self, path: str | Path) -> str: ...
    def tags(self, path: str | Path) -> list[str]: ...
    def commits(self, path: str | Path, since: str | None = None) -> list[dict[str, Any]]: ...
    def tag_commit(self, path: str | Path, tag: str) -> str | None: ...


def backend_for(path: str | Path | None = None) -> VCSBackend:
    """Select the installed backend by repository markers."""
    from . import git

    if git.available(path):
        return git
    raise RuntimeError("no supported version-control repository found (currently supported: Git)")
