"""Recursive discovery of supported project version metadata."""

from __future__ import annotations

import os
from pathlib import Path

from .discovery import VERSION_FILES, _candidate
from .semver import Version

# These directories contain generated environments or dependency/build trees,
# not project-owned metadata. Other directories, including archives, are scanned.
PRUNED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "build",
    "dist",
    "target",
}

YAML_VERSION_KEYS = (
    "control.Version",
    "version",
    "package.version",
)


def _yaml_sources(path: Path, relative: str):
    """Return the one unambiguous supported version field in a YAML document."""
    try:
        from ruamel.yaml import YAML

        parser = YAML(typ="safe")
        data = parser.load(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    matches = []
    for dotted_key in YAML_VERSION_KEYS:
        value = data
        try:
            for part in dotted_key.split("."):
                value = value[part]
        except (KeyError, TypeError):
            continue
        try:
            Version.parse(str(value))
        except (TypeError, ValueError):
            continue
        matches.append({"type": "yaml", "file": relative, "key": dotted_key})

    # A YAML file with multiple plausible version fields is ambiguous. Do not
    # guess which field belongs to the project package.
    return matches if len(matches) == 1 else []


def discover_sync_targets(root, canonical_source=None):
    """Find supported version metadata recursively, without changing files.

    Only known metadata filenames and unambiguous YAML version fields qualify.
    Invalid, unsupported, or ambiguous files are ignored. Returned paths are
    relative to the project root and can be passed directly to synchronization.
    """
    root = Path(root).resolve()
    canonical_path = None
    if canonical_source:
        canonical_path = (root / canonical_source["file"]).resolve()

    found = []
    seen = set()
    for current, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name for name in directories if name not in PRUNED_DIRECTORIES
        )
        current_path = Path(current)
        for filename in sorted(filenames):
            path = current_path / filename
            if path.is_symlink():
                continue
            relative = path.relative_to(root).as_posix()
            if canonical_path and path.resolve() == canonical_path:
                continue

            candidates = []
            for known_name, kind, key in VERSION_FILES:
                if known_name == "debian/changelog":
                    matches_name = filename == "changelog" and current_path.name == "debian"
                elif known_name == "debian/control":
                    matches_name = filename == "control" and current_path.name == "debian"
                    if matches_name:
                        candidate = _candidate(root, relative, "debian", None)
                        if candidate:
                            candidates.append(candidate["source"])
                    continue
                else:
                    matches_name = filename == Path(known_name).name
                if matches_name:
                    candidate = _candidate(root, relative, kind, key)
                    if candidate:
                        candidates.append(candidate["source"])

            if path.suffix.lower() in {".yaml", ".yml"}:
                candidates.extend(_yaml_sources(path, relative))

            # One file can match multiple known filename rules. Keep only one
            # source descriptor; ambiguous YAML documents were already rejected.
            unique = {
                (item["type"], item["file"], item.get("key")): item
                for item in candidates
            }
            for key in sorted(unique):
                source = unique[key]
                try:
                    from .version_sources import read_version

                    Version.parse(read_version(root, source))
                except Exception:
                    continue
                identity = (source["file"], source["type"], source.get("key"))
                if identity not in seen:
                    seen.add(identity)
                    found.append(source)

    return sorted(found, key=lambda item: (item["file"].count("/"), item["file"], item["type"]))
