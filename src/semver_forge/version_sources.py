"""Version source adapters for project metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from .errors import ConfigError


def _path(root, file):
    base = Path(root).resolve()
    path = (base / file).resolve()
    if not path.is_relative_to(base):
        raise ConfigError(f"path escapes project root: {file}")
    return path


def read_version(root, source):
    path = _path(root, source["file"])
    kind = source["type"]
    if not path.is_file():
        raise ConfigError(f"version source missing: {path}")
    text = path.read_text(encoding="utf-8")
    key = source.get("key")
    if kind == "text":
        return text.strip()
    if kind in {"json", "toml"}:
        data = json.loads(text) if kind == "json" else tomllib.loads(text)
        dotted_key = key or ("version" if kind == "json" else "project.version")
        for part in dotted_key.split("."):
            data = data[part]
        return str(data)
    if kind == "shell":
        variable = key or "VERSION"
        matches = re.findall(
            rf"^\s*{re.escape(variable)}\s*=\s*[\"']?([^\"'\n#]+)",
            text,
            re.M,
        )
        if len(matches) != 1:
            raise ConfigError(f"{path}: expected exactly one {variable}= assignment")
        return matches[0].strip()
    if kind == "debian":
        matches = re.findall(r"^Version:\s*(\S+)\s*$", text, re.M)
        if len(matches) != 1:
            raise ConfigError(f"{path}: expected exactly one Version field")
        return matches[0]
    if kind == "debian-changelog":
        lines = text.splitlines()
        match = re.match(
            r"^(\S+\s+\()([^)]+)(\)\s+\S+;\s*urgency=.*)$",
            lines[0] if lines else "",
        )
        if not match:
            raise ConfigError(f"{path}: expected a standard Debian changelog header")
        return match.group(2)
    if kind == "yaml":
        raise ConfigError("YAML support requires an explicit adapter; no YAML parser is bundled")
    raise ConfigError(f"unsupported version source type: {kind}")


def render_version(root, source, version):
    path = _path(root, source["file"])
    kind = source["type"]
    text = path.read_text(encoding="utf-8")
    key = source.get("key")
    if kind == "text":
        return version + "\n"
    if kind == "json":
        data = json.loads(text)
        parts = (key or "version").split(".")
        current = data
        for part in parts[:-1]:
            current = current[part]
        current[parts[-1]] = version
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if kind == "toml":
        dotted_key = key or "project.version"
        parts = dotted_key.split(".")
        section = ".".join(parts[:-1])
        field = parts[-1]
        lines = text.splitlines(keepends=True)
        section_pattern = re.compile(r"^\s*\[" + re.escape(section) + r"\]\s*(?:#.*)?$")
        field_pattern = re.compile(
            r"^(\s*" + re.escape(field) + r"\s*=\s*)([^#\r\n]+?)(\s*(?:#.*)?(?:\r?\n)?)$"
        )
        in_section = False
        matches = []
        table_pattern = re.compile(r"^\s*\[[^\]]+\]\s*(?:#.*)?$")
        for index, line in enumerate(lines):
            candidate = line.rstrip("\r\n")
            if table_pattern.match(candidate):
                in_section = bool(section_pattern.match(candidate))
            elif in_section:
                match = field_pattern.match(line)
                if match:
                    matches.append((index, match))
        if len(matches) != 1:
            raise ConfigError(
                f"{path}: expected exactly one {dotted_key} TOML field in [{section}]"
            )
        index, match = matches[0]
        lines[index] = match.group(1) + json.dumps(version) + match.group(3)
        return "".join(lines)
    if kind == "shell":
        variable = key or "VERSION"
        pattern = (
            rf"^(\s*{re.escape(variable)}\s*=\s*)([\"']?)"
            rf"[^\"'\n#]+([\"']?\s*(?:#.*)?)$"
        )
        updated, count = re.subn(
            pattern,
            lambda match: match.group(1) + match.group(2) + version + match.group(3),
            text,
            count=1,
            flags=re.M,
        )
        if count != 1:
            raise ConfigError(f"{path}: expected exactly one {variable}= assignment")
        return updated
    if kind == "debian":
        updated, count = re.subn(
            r"^(Version:\s*)\S+(\s*)$",
            lambda match: match.group(1) + version + match.group(2),
            text,
            count=1,
            flags=re.M,
        )
        if count != 1:
            raise ConfigError(f"{path}: expected exactly one Version field")
        return updated
    if kind == "debian-changelog":
        updated, count = re.subn(
            r"^(\S+\s+\()[^)]+(\)\s+\S+;\s*urgency=.*)$",
            lambda match: match.group(1) + version + match.group(2),
            text,
            count=1,
            flags=re.M,
        )
        if count != 1:
            raise ConfigError(f"{path}: expected a standard Debian changelog header")
        return updated
    if kind == "yaml":
        raise ConfigError("YAML support requires an explicit adapter; no YAML parser is bundled")
    raise ConfigError(f"unsupported version source type: {kind}")
