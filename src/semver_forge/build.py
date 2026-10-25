import os
import subprocess
from pathlib import Path

from .errors import BuildFailure, ConfigError, TestFailure


def run_commands(commands, root, stage, dry_run=False):
    if not commands:
        return {"configured": False, "commands": [], "status": "not_configured"}
    results = []
    for item in commands:
        if isinstance(item, str):
            cmd = [item]
            cwd = root
            timeout = 300
            shell = True
            env = {}
        else:
            cmd = item.get("args") or item.get("command")
            if isinstance(cmd, str):
                cmd = [cmd]
                shell = True
            else:
                shell = False
            cwd = (Path(root) / item.get("cwd", ".")).resolve()
            if not cwd.is_relative_to(Path(root).resolve()):
                raise ConfigError(f"{stage} command working directory escapes project root")
            timeout = int(item.get("timeout", 300))
            env = item.get("env", {})
        if dry_run:
            results.append({"command": cmd, "status": "dry_run"})
            continue
        e = os.environ.copy()
        e.update({str(k): str(v) for k, v in env.items()})
        try:
            p = subprocess.run(
                cmd,
                cwd=cwd,
                env=e,
                shell=shell,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as ex:
            raise (TestFailure if stage == "test" else BuildFailure)(
                f"{stage} command timed out: {cmd}"
            ) from ex
        results.append(
            {"command": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
        )
        if p.returncode:
            raise (TestFailure if stage == "test" else BuildFailure)(
                f"{stage} command failed ({p.returncode}): {cmd}\n{p.stderr.strip()}"
            )
    return {"configured": True, "commands": results, "status": "dry_run" if dry_run else "passed"}
