"""Portable best-effort exclusive lock based on atomic file creation."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path

from .errors import SafetyError


@contextmanager
def lock(path: str | Path, timeout: float = 0):
    lock_path = Path(path)
    fd = None
    start = time.monotonic()

    while fd is None:
        try:
            fd = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as exc:
            if time.monotonic() - start >= timeout:
                raise SafetyError(
                    f"release lock exists: {lock_path}; verify no release is running, "
                    "then remove stale lock manually"
                ) from exc
            time.sleep(0.1)

    try:
        os.write(fd, f"pid={os.getpid()}\n".encode())
        os.close(fd)
        fd = None
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
