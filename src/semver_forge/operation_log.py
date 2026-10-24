"""Bounded local diagnostics for SemVer Forge's own operations.

This logger never discovers, creates, stages, ignores, or modifies project log files.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import threading
import traceback

_MAX_BYTES = 10 * 1024 * 1024
_LOCK = threading.RLock()


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
        event["message"] = str(error)[:2000]
        event["traceback"] = "".join(traceback.format_exception(error))[-12000:]
    line = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    with _LOCK:
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
