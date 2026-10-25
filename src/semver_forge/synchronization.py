from __future__ import annotations

import os
import tempfile

from .errors import ConfigError
from .semver import SemVerError, Version
from .version_sources import _path, read_version, render_version


def sync(root, cfg, version, dry_run=False):
    try:
        version = str(Version.parse(str(version)))
    except SemVerError as exc:
        raise ConfigError(f"invalid target version {version!r}: {exc}") from exc

    sources = [cfg["version"]["source"], *cfg.get("sync", {}).get("targets", [])]
    changes = []
    for source in sources:
        path = _path(root, source["file"])
        if not path.exists():
            raise ConfigError(f"synchronization target missing: {path}")
        old = read_version(root, source)
        new = render_version(root, source, version)
        changes.append((path, old, new, source))

    if dry_run:
        return [
            {
                "file": str(path),
                "old_version": old,
                "new_version": version,
                "changed": old != version,
            }
            for path, old, _new, _source in changes
        ]

    # Validate every file before any writes; backups are in memory and restored on failure.
    originals = {path: path.read_bytes() for path, _, _, _ in changes}
    written = []
    try:
        for path, old, new, _source in changes:
            if old == version:
                continue
            fd, temporary_path = tempfile.mkstemp(
                prefix=".semver-forge-",
                dir=path.parent,
            )
            try:
                with os.fdopen(
                    fd,
                    "w",
                    encoding="utf-8",
                    newline="",
                ) as file_handle:
                    file_handle.write(new)
                    file_handle.flush()
                    os.fsync(file_handle.fileno())
                os.chmod(temporary_path, path.stat().st_mode)
                os.replace(temporary_path, path)
                written.append(path)
            finally:
                if os.path.exists(temporary_path):
                    os.unlink(temporary_path)

        for path, _old, _new, source in changes:
            if read_version(root, source) != version:
                raise ConfigError(f"post-write verification failed for {path}")
    except Exception:
        for path in reversed(written):
            fd, temporary_path = tempfile.mkstemp(
                prefix=".semver-forge-rollback-",
                dir=path.parent,
            )
            try:
                with os.fdopen(fd, "wb") as file_handle:
                    file_handle.write(originals[path])
                    file_handle.flush()
                    os.fsync(file_handle.fileno())
                os.replace(temporary_path, path)
            finally:
                if os.path.exists(temporary_path):
                    os.unlink(temporary_path)
        raise

    return [
        {
            "file": str(path),
            "old_version": old,
            "new_version": version,
            "changed": old != version,
        }
        for path, old, _new, _source in changes
    ]
