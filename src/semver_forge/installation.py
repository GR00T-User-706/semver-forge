"""User-local installation and removal of files owned by semver-forge."""

import os
import shlex
import shutil
import sys
from pathlib import Path


def install(prefix=None):
    source = Path(__file__).resolve().parents[2]
    prefix = (
        Path(prefix or os.environ.get("SEMVER_FORGE_HOME", Path.home() / ".local"))
        .expanduser()
        .resolve()
    )
    bin_dir = prefix / "bin"
    lib_dir = prefix / "lib" / "semver-forge"
    man1_dir = prefix / "share" / "man" / "man1"
    man5_dir = prefix / "share" / "man" / "man5"
    launchers = {
        "svf": bin_dir / "svf",
        "semver-forge": bin_dir / "semver-forge",
    }
    manual_sources = {
        "svf.1": source / "man" / "svf.1",
        "semver-forge.1": source / "man" / "semver-forge.1",
        "svf-config.5": source / "man" / "svf-config.5",
    }
    manual_destinations = {
        "svf.1": man1_dir / "svf.1",
        "semver-forge.1": man1_dir / "semver-forge.1",
        "svf-config.5": man5_dir / "svf-config.5",
    }

    # Preflight every destination before creating or copying anything.
    if lib_dir.exists():
        raise FileExistsError(f"installation already exists at {lib_dir}; refusing to overwrite it")
    for launcher in launchers.values():
        if launcher.exists():
            raise FileExistsError(f"refusing to overwrite existing launcher: {launcher}")
    for name, destination in manual_destinations.items():
        if manual_sources[name].is_file() and destination.exists():
            raise FileExistsError(f"refusing to overwrite existing man page: {destination}")

    bin_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "src" / "semver_forge", lib_dir / "semver_forge")
    launcher_content = (
        "#!/bin/sh\n"
        f"PYTHONPATH={shlex.quote(str(lib_dir))}${{PYTHONPATH:+:$PYTHONPATH}} "
        f'exec {shlex.quote(sys.executable)} -m semver_forge "$@"\n'
    )
    for launcher in launchers.values():
        launcher.write_text(launcher_content, encoding="utf-8")
        launcher.chmod(0o755)

    installed_manuals = {}
    for name, bundled in manual_sources.items():
        if bundled.is_file():
            destination = manual_destinations[name]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundled, destination)
            installed_manuals[name] = str(destination)

    return {
        "launcher": str(launchers["svf"]),
        "compatibility_launcher": str(launchers["semver-forge"]),
        "library": str(lib_dir),
        "manpage": installed_manuals.get("svf.1"),
        "config_manpage": installed_manuals.get("svf-config.5"),
    }


def uninstall(prefix=None):
    prefix = (
        Path(prefix or os.environ.get("SEMVER_FORGE_HOME", Path.home() / ".local"))
        .expanduser()
        .resolve()
    )
    launchers = [
        prefix / "bin" / "svf",
        prefix / "bin" / "semver-forge",
    ]
    lib_dir = prefix / "lib" / "semver-forge"
    manuals = [
        prefix / "share" / "man" / "man1" / "svf.1",
        prefix / "share" / "man" / "man1" / "semver-forge.1",
        prefix / "share" / "man" / "man5" / "svf-config.5",
    ]

    # Validate owned-file markers before deleting any installation component.
    for launcher in launchers:
        if launcher.exists():
            content = launcher.read_text(errors="replace")
            if "PYTHONPATH=" not in content or "-m semver_forge" not in content:
                raise ValueError(f"refusing to remove unrecognized launcher: {launcher}")

    for manual in manuals:
        if not manual.exists():
            continue
        content = manual.read_text(errors="replace")
        if manual.name == "svf.1" and not content.startswith(".TH SVF "):
            raise ValueError(f"refusing to remove unrecognized man page: {manual}")
        if manual.name == "svf-config.5" and not content.startswith(".TH SVF-CONFIG "):
            raise ValueError(f"refusing to remove unrecognized man page: {manual}")
        if manual.name == "semver-forge.1" and not (
            content.startswith(".so man1/svf.1") or content.startswith(".TH SEMVER-FORGE ")
        ):
            raise ValueError(f"refusing to remove unrecognized man page: {manual}")

    for launcher in launchers:
        if launcher.exists():
            launcher.unlink()
    if lib_dir.exists():
        shutil.rmtree(lib_dir)
    for manual in manuals:
        if manual.exists():
            manual.unlink()

    return {
        "launchers_removed": [str(path) for path in launchers if not path.exists()],
        "library_removed": str(lib_dir),
        "manpages_removed": [str(path) for path in manuals if not path.exists()],
    }
