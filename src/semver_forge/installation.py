"""User-local installation and removal of files owned by semver-forge."""
from pathlib import Path
import os
import shlex
import shutil
import sys


def install(prefix=None):
    source = Path(__file__).resolve().parents[2]
    prefix = Path(prefix or os.environ.get("SEMVER_FORGE_HOME", Path.home() / ".local")).expanduser().resolve()
    bin_dir = prefix / "bin"
    lib_dir = prefix / "lib" / "semver-forge"
    man_dir = prefix / "share" / "man" / "man1"
    launcher = bin_dir / "semver-forge"
    manpage = man_dir / "semver-forge.1"

    # Preflight every destination before creating or copying anything.
    if lib_dir.exists():
        raise FileExistsError(f"installation already exists at {lib_dir}; refusing to overwrite it")
    if launcher.exists():
        raise FileExistsError(f"refusing to overwrite existing launcher: {launcher}")
    bundled_man = source / "man" / "semver-forge.1"
    if bundled_man.is_file() and manpage.exists():
        raise FileExistsError(f"refusing to overwrite existing man page: {manpage}")

    bin_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "src" / "semver_forge", lib_dir / "semver_forge")
    launcher.write_text(
        "#!/bin/sh\n"
        f"PYTHONPATH={shlex.quote(str(lib_dir))}${{PYTHONPATH:+:$PYTHONPATH}} "
        f"exec {shlex.quote(sys.executable)} -m semver_forge \"$@\"\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    installed_man = None
    if bundled_man.is_file():
        man_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundled_man, manpage)
        installed_man = str(manpage)
    return {"launcher": str(launcher), "library": str(lib_dir), "manpage": installed_man}


def uninstall(prefix=None):
    prefix = Path(prefix or os.environ.get("SEMVER_FORGE_HOME", Path.home() / ".local")).expanduser().resolve()
    launcher = prefix / "bin" / "semver-forge"
    lib_dir = prefix / "lib" / "semver-forge"
    manpage = prefix / "share" / "man" / "man1" / "semver-forge.1"

    # Validate owned-file markers before deleting any installation component.
    if launcher.exists():
        content = launcher.read_text(errors="replace")
        if "PYTHONPATH=" not in content or "-m semver_forge" not in content:
            raise ValueError(f"refusing to remove unrecognized launcher: {launcher}")
    if manpage.exists() and not manpage.read_text(errors="replace").startswith(".TH SEMVER-FORGE "):
        raise ValueError(f"refusing to remove unrecognized man page: {manpage}")

    if launcher.exists():
        launcher.unlink()
    if lib_dir.exists():
        shutil.rmtree(lib_dir)
    if manpage.exists():
        manpage.unlink()
    return {
        "launcher_removed": str(launcher),
        "library_removed": str(lib_dir),
        "manpage_removed": str(manpage),
    }
