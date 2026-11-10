"""System, user, and project configuration scope management."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from .config import DEFAULTS, find_config, merge
from .errors import ConfigError


def scope_paths(root: Path) -> dict[str, Path]:
    prefix = os.environ.get("PREFIX")
    system = Path(prefix) / "etc" / "svfconfig" if prefix else Path("/etc/svfconfig")
    return {
        "system": system,
        "global": Path.home() / ".svfconfig",
        "project": find_config(root) or Path(root) / ".semver-forge.toml",
    }


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"invalid configuration {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"configuration root must be a TOML table: {path}")
    return data


def effective_config(root: Path) -> tuple[dict, dict, list[str]]:
    paths = scope_paths(root)
    layers = {}
    for scope in ("system", "global", "project"):
        layers[scope] = _read(paths[scope])
    merged = merge(DEFAULTS, layers["system"])
    merged = merge(merged, layers["global"])
    merged = merge(merged, layers["project"])
    unknown = []
    known = {key: set(value) for key, value in DEFAULTS.items()}
    for scope, data in layers.items():
        for section, values in data.items():
            if section not in known:
                unknown.append(f"{scope}:{section}")
            elif isinstance(values, dict):
                unknown.extend(
                    f"{scope}:{section}.{key}" for key in values if key not in known[section]
                )
    from .semver import SemVerError, Version

    try:
        Version.parse(str(merged["version"]["initial"]))
    except (SemVerError, KeyError, TypeError) as exc:
        raise ConfigError(f"effective config [version].initial is invalid: {exc}") from exc
    source = merged.get("version", {}).get("source")
    supported_types = {
        "text",
        "json",
        "toml",
        "shell",
        "debian",
        "debian-changelog",
        "yaml",
    }
    if (
        not isinstance(source, dict)
        or source.get("type") not in supported_types
        or not isinstance(source.get("file"), str)
        or not source.get("file")
        or ("key" in source and not isinstance(source["key"], str))
    ):
        raise ConfigError("effective config [version].source must define a supported type and file")
    targets = merged.get("sync", {}).get("targets", [])
    if not isinstance(targets, list):
        raise ConfigError("effective config [sync].targets must be an array")
    discovery_keys = merged.get("sync", {}).get("discovery_keys", [])
    if not isinstance(discovery_keys, list) or not all(isinstance(key, str) and key for key in discovery_keys):
        raise ConfigError("effective config [sync].discovery_keys must be an array of non-empty strings")
    for index, target in enumerate(targets):
        if (
            not isinstance(target, dict)
            or target.get("type") not in supported_types
            or not isinstance(target.get("file"), str)
            or not target.get("file")
            or ("key" in target and not isinstance(target["key"], str))
        ):
            raise ConfigError(f"effective config [sync].targets[{index}] is invalid")
    return merged, paths, unknown


def _toml_value(value: str):
    try:
        return tomllib.loads("value = " + value)["value"]
    except (tomllib.TOMLDecodeError, TypeError) as exc:
        raise ConfigError(f"invalid TOML value {value!r}: {exc}") from exc


def _render_toml_value(value) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_render_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        entries = []
        for key, item in value.items():
            rendered_key = (
                key
                if re.fullmatch(r"[A-Za-z0-9_-]+", str(key))
                else json.dumps(str(key), ensure_ascii=False)
            )
            entries.append(f"{rendered_key} = {_render_toml_value(item)}")
        return "{ " + ", ".join(entries) + " }"
    raise ConfigError(f"unsupported TOML value type: {type(value).__name__}")


def _set_text(text: str, dotted_key: str, value) -> str:
    parts = dotted_key.split(".")
    if not parts or any(not re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in parts):
        raise ConfigError(f"invalid configuration key: {dotted_key}")
    table = ".".join(parts[:-1])
    field = parts[-1]
    rendered = _render_toml_value(value)
    lines = text.splitlines(keepends=True)
    header = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
    assignment = re.compile(r"^(\s*" + re.escape(field) + r"\s*=\s*)(.*?)(\s+#.*)?$")
    current = ""
    matches = []
    for index, line in enumerate(lines):
        candidate = line.rstrip("\r\n")
        match = header.match(candidate)
        if match:
            current = match.group(1).strip()
        elif current == table:
            found = assignment.match(candidate)
            if found:
                matches.append((index, found.group(1), found.group(3) or ""))
    if len(matches) > 1:
        raise ConfigError(f"configuration key appears more than once: {dotted_key}")
    if matches:
        index, prefix, comment = matches[0]
        newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
        lines[index] = prefix + rendered + comment + newline
        return "".join(lines)
    if not table:
        # Root-level keys are inserted before the first table.
        insert_at = next(
            (i for i, line in enumerate(lines) if header.match(line.rstrip("\r\n"))),
            len(lines),
        )
        lines.insert(insert_at, f"{field} = {rendered}\n")
        return "".join(lines)
    table_header = f"[{table}]"
    table_indexes = [
        i
        for i, line in enumerate(lines)
        if (match := header.match(line.rstrip("\r\n"))) and match.group(1).strip() == table
    ]
    if table_indexes:
        start = table_indexes[0] + 1
        end = next(
            (i for i in range(start, len(lines)) if header.match(lines[i].rstrip("\r\n"))),
            len(lines),
        )
        lines.insert(end, f"{field} = {rendered}\n")
        return "".join(lines)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    if lines and lines[-1].strip():
        lines.append("\n")
    lines.extend([table_header + "\n", f"{field} = {rendered}\n"])
    return "".join(lines)


def _unset_text(text: str, dotted_key: str) -> str:
    parts = dotted_key.split(".")
    if not parts or any(not re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in parts):
        raise ConfigError(f"invalid configuration key: {dotted_key}")
    table, field = ".".join(parts[:-1]), parts[-1]
    header = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
    assignment = re.compile(r"^\s*" + re.escape(field) + r"\s*=")
    lines = text.splitlines(keepends=True)
    current = ""
    matches = []
    for index, line in enumerate(lines):
        match = header.match(line.rstrip("\r\n"))
        if match:
            current = match.group(1).strip()
        elif current == table and assignment.match(line):
            matches.append(index)
    if len(matches) > 1:
        raise ConfigError(f"configuration key appears more than once: {dotted_key}")
    if not matches:
        raise ConfigError(f"configuration key not found: {dotted_key}")
    del lines[matches[0]]
    return "".join(lines)


def _atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".svfconfig-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(temporary, path.stat().st_mode)
        else:
            os.chmod(temporary, 0o600 if path.name == ".svfconfig" else 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def config_get(root: Path, key: str, scope: str | None = None):
    if scope is None:
        value, paths, _unknown = effective_config(root)
        source = "defaults"
        for candidate in ("system", "global", "project"):
            current = _read(paths[candidate])
            try:
                for part in key.split("."):
                    current = current[part]
                source = candidate
            except (KeyError, TypeError):
                pass
    else:
        value = _read(scope_paths(root)[scope])
        source = scope
    try:
        for part in key.split("."):
            value = value[part]
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"configuration key not found: {key}") from exc
    return {"key": key, "value": value, "source": source}


def config_write(root: Path, scope: str, key: str, value: str | None, unset=False):
    paths = scope_paths(root)
    path = paths[scope]
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    # Parse before and after the edit so malformed files are never overwritten.
    try:
        if text.strip():
            tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML configuration {path}: {exc}") from exc
    if unset:
        updated = _unset_text(text, key)
    else:
        parsed_value = _toml_value(value) if isinstance(value, str) else value
        updated = _set_text(text, key, parsed_value)
    try:
        after = tomllib.loads(updated)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"configuration update would produce invalid TOML: {exc}") from exc
    if not isinstance(after, dict):
        raise ConfigError("configuration root must be a TOML table")
    existed = path.exists()
    original = text
    _atomic_write(path, updated)
    try:
        effective_config(root)
    except Exception:
        if existed:
            _atomic_write(path, original)
        else:
            path.unlink(missing_ok=True)
        raise
    return {"scope": scope, "file": str(path), "key": key, "unset": unset}


def config_edit(root: Path, scope: str):
    path = scope_paths(root)[scope]
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    command = shlex.split(editor)
    if not command:
        raise ConfigError("EDITOR or VISUAL is empty")
    executable = shutil.which(command[0])
    if not executable:
        raise ConfigError(f"editor not found: {command[0]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    original = path.read_text(encoding="utf-8") if existed else ""
    if not existed:
        path.touch(mode=0o600 if scope == "global" else 0o644)
    result = subprocess.run([executable, *command[1:], str(path)], check=False)
    if result.returncode:
        raise ConfigError(f"editor exited with status {result.returncode}")
    try:
        _read(path)
        effective_config(root)
    except Exception:
        if existed:
            _atomic_write(path, original)
        else:
            path.unlink(missing_ok=True)
        raise
    return {"scope": scope, "file": str(path)}


def _source_map(value, layers, prefix=""):
    sources = {}
    if isinstance(value, dict):
        for key, child in value.items():
            dotted = f"{prefix}.{key}" if prefix else key
            sources.update(_source_map(child, layers, dotted))
    else:
        source = "defaults"
        for scope in ("system", "global", "project"):
            current = layers[scope]
            try:
                for part in prefix.split("."):
                    current = current[part]
                source = scope
            except (KeyError, TypeError):
                pass
        sources[prefix] = source
    return sources


def config_report(root: Path, scope: str | None = None):
    if scope is not None:
        path = scope_paths(root)[scope]
        return {
            "scope": scope,
            "file": str(path),
            "exists": path.is_file(),
            "values": _read(path),
        }
    merged, paths, unknown = effective_config(root)
    layers = {}
    for scope, path in paths.items():
        layers[scope] = {
            "file": str(path),
            "exists": path.is_file(),
            "values": _read(path),
        }
    return {
        "precedence": ["system", "global", "project"],
        "scopes": layers,
        "effective": merged,
        "sources": _source_map(merged, {scope: layers[scope]["values"] for scope in layers}),
        "unknown_keys": unknown,
    }
