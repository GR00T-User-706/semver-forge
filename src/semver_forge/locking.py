"""Portable best-effort exclusive lock based on atomic file creation."""
from pathlib import Path
import os, time
from contextlib import contextmanager
from .errors import SafetyError
@contextmanager
def lock(path, timeout=0):
    p=Path(path); fd=None; start=time.monotonic()
    while fd is None:
        try: fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError:
            if time.monotonic()-start>=timeout: raise SafetyError(f'release lock exists: {p}; verify no release is running, then remove stale lock manually')
            time.sleep(.1)
    try:
        os.write(fd,f'pid={os.getpid()}\n'.encode()); os.close(fd); fd=None
        yield
    finally:
        if fd is not None: os.close(fd)
        try: p.unlink()
        except FileNotFoundError: pass
