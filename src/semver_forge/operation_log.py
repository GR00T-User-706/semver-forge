"""Bounded local diagnostics for SemVer Forge's own operations.

This logger never discovers, creates, stages, ignores, or modifies project log files.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path
import tempfile
import threading
import traceback

_MAX_BYTES = 10 * 1024 * 1024
_LOCK = threading.RLock()


@contextmanager
def _process_lock(target: Path):
    """Serialize log rewrites across processes on POSIX and Windows."""
    lock_file = target.with_name(target.name + ".lock")
    with lock_file.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            stream.seek(0)
            if stream.read(1) == b"":
                stream.seek(0)
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _redact(value: str) -> str:
    """Mask common credential assignments before diagnostics reach disk."""
    return re.sub(
        r"(?i)(token|password|secret|api[_-]?key|authorization)(\s*[:=]\s*)([^\s,;]+)",
        r"\1\2[REDACTED]",
        value,
    )


def log_path() -> Path:
    """Return SemVer Forge's user-local diagnostic log path."""
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "semver-forge" / "semver-forge.log"


def record(level: str, action: str, outcome: str, *, error: BaseException | None = None,
           path: Path | None = None, max_bytes: int = _MAX_BYTES) -> None:
    """Append one structured event and retain the newest max_bytes of history."""
    target = path or log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "level": level.upper(),
        "action": action,
        "outcome": outcome,
    }
    if error is not None:
        event["exception"] = type(error).__name__
        event["message"] = _redact(str(error))[:2000]
        event["traceback"] = _redact("".join(traceback.format_exception(error)))[-12000:]
    line = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    with _LOCK, _process_lock(target):
        existing = target.read_bytes() if target.exists() else b""
        data = existing + line
        if len(data) > max_bytes:
            data = data[-max_bytes:]
            newline = data.find(b"\n")
            if newline >= 0:
                data = data[newline + 1:]
        fd, temp_name = tempfile.mkstemp(prefix=".semver-forge-log-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
