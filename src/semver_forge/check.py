"""Read-only project and configuration diagnostics."""

from __future__ import annotations

from pathlib import Path

from .config_scopes import config_report, effective_config, scope_paths
from .errors import ConfigError
from .metadata_discovery import discover_sync_targets
from .semver import Version
from .version_sources import read_version


def inspect_project(root: Path, project_config: Path | None = None) -> dict:
    root = Path(root).resolve()
    try:
        cfg, _paths, unknown = effective_config(root)
    except ConfigError as exc:
        try:
            paths = scope_paths(root)
        except ConfigError as path_error:
            return {
                "project": {"root": str(root), "name": None},
                "canonical": {
                    "source": None,
                    "version": None,
                    "status": "configuration_error",
                },
                "synchronization": [],
                "discovery": {"files": [], "unconfigured": [], "errors": []},
                "configuration": {
                    "precedence": ["system", "global", "project"],
                    "scopes": {},
                    "effective": None,
                    "sources": {},
                    "unknown_keys": [],
                },
                "errors": [str(exc), str(path_error)],
            }
        scopes = {}
        for scope, path in paths.items():
            try:
                from .config_scopes import _read

                values = _read(path)
                scopes[scope] = {
                    "file": str(path),
                    "exists": path.is_file(),
                    "values": values,
                }
            except ConfigError as scope_error:
                scopes[scope] = {
                    "file": str(path),
                    "exists": path.is_file(),
                    "error": str(scope_error),
                }
        return {
            "project": {"root": str(root), "name": None},
            "canonical": {
                "source": None,
                "version": None,
                "status": "configuration_error",
            },
            "synchronization": [],
            "discovery": {"files": [], "unconfigured": [], "errors": []},
            "configuration": {
                "precedence": ["system", "global", "project"],
                "scopes": scopes,
                "effective": None,
                "sources": {},
                "unknown_keys": [],
            },
            "errors": [str(exc)],
        }
    source = cfg["version"]["source"]
    result = {
        "project": {
            "root": str(root),
            "name": cfg.get("project", {}).get("name") or root.name,
        },
        "canonical": {
            "source": source,
            "version": None,
            "status": "missing",
        },
        "synchronization": [],
        "discovery": {"files": [], "unconfigured": [], "errors": []},
        "configuration": config_report(root),
        "errors": [],
    }
    current = None
    if not (root / source["file"]).exists():
        message = f"canonical version source missing: {source['file']}"
        result["canonical"].update(status="missing", error=message)
        result["errors"].append(message)
    else:
        try:
            current = Version.parse(read_version(root, source))
            result["canonical"].update(version=str(current), status="valid")
        except OSError as exc:
            result["canonical"].update(status="unreadable", error=str(exc))
            result["errors"].append(str(exc))
        except (ConfigError, ValueError, TypeError, KeyError) as exc:
            result["canonical"].update(status="invalid", error=str(exc))
            result["errors"].append(str(exc))

    configured = cfg.get("sync", {}).get("targets", [])
    targets = [source, *configured]
    seen = set()
    by_file = {}
    for target in targets:
        by_file.setdefault(target.get("file"), []).append(target)
    conflicts = {
        filename: definitions
        for filename, definitions in by_file.items()
        if len({(item.get("type"), item.get("key")) for item in definitions}) > 1
    }
    for target in targets:
        identity = (target.get("file"), target.get("type"), target.get("key"))
        if identity in seen:
            continue
        seen.add(identity)
        item = {
            "file": target.get("file"),
            "type": target.get("type"),
            "key": target.get("key"),
        }
        if target.get("file") in conflicts:
            item.update(status="conflicting", definitions=conflicts[target.get("file")])
            result["synchronization"].append(item)
            continue
        if not (root / str(target.get("file", ""))).exists():
            item["status"] = "missing"
            result["synchronization"].append(item)
            continue
        try:
            actual = Version.parse(read_version(root, target))
            status = (
                "matching"
                if current and actual == current
                else "drift"
                if current
                else "canonical_unavailable"
            )
            item.update(actual_version=str(actual), status=status)
        except OSError as exc:
            item.update(status="unreadable", error=str(exc))
        except (ConfigError, ValueError, TypeError, KeyError) as exc:
            item.update(status="invalid", error=str(exc))
        result["synchronization"].append(item)

    try:
        discovered = discover_sync_targets(root, source)
        configured_ids = {
            (item.get("file"), item.get("type"), item.get("key")) for item in configured
        }
        file_status = []
        for item in discovered:
            identity = (item.get("file"), item.get("type"), item.get("key"))
            file_status.append({**item, "configured": identity in configured_ids})
        result["discovery"]["files"] = file_status
        result["discovery"]["unconfigured"] = [
            item for item in file_status if not item["configured"]
        ]
    except (ConfigError, OSError) as exc:
        result["discovery"]["errors"].append(str(exc))
        result["errors"].append(str(exc))
    result["configuration"]["unknown_keys"] = unknown
    return result
