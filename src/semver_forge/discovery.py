"""Read-only project inspection used by semver-forge init."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .semver import Version

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


VERSION_FILES = (
    ("pyproject.toml", "toml", "project.version"),
    ("package.json", "json", "version"),
    ("Cargo.toml", "toml", "package.version"),
    ("VERSION", "text", None),
    ("version.txt", "text", None),
    ("version", "text", None),
    ("debian/changelog", "debian-changelog", None),
    ("PKGBUILD", "shell", "pkgver"),
)


def _read_source(root: Path, source: dict) -> str:
    text = (root / source["file"]).read_text(encoding="utf-8")
    kind = source["type"]
    if kind == "text":
        value = text.strip()
    elif kind in {"toml", "json"}:
        data = tomllib.loads(text) if kind == "toml" else json.loads(text)
        for part in source.get("key", "").split("."):
            if part:
                data = data[part]
        value = str(data)
    elif kind == "debian-changelog":
        first_line = text.splitlines()[0] if text.splitlines() else ""
        match = re.match(r"^\S+\s+\(([^)]+)\)\s+\S+;\s*urgency=", first_line)
        if not match:
            raise ValueError("expected a standard Debian changelog header")
        value = match.group(1)
    elif kind == "shell":
        key = source["key"]
        matches = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(key + "=") or stripped.startswith(key + " ="):
                matches.append(stripped.split("=", 1)[1].split("#", 1)[0].strip().strip("'\""))
        if len(matches) != 1:
            raise ValueError(f"expected one {key} assignment")
        value = matches[0]
    else:
        raise ValueError(f"unsupported version source: {kind}")
    Version.parse(value)
    return value


def _candidate(root: Path, filename: str, kind: str, key: str | None):
    path = root / filename
    if not path.is_file():
        return None
    source = {"type": kind, "file": filename}
    if key:
        source["key"] = key
    try:
        value = _read_source(root, source)
    except (
        OSError, ValueError, KeyError, TypeError,
        json.JSONDecodeError, tomllib.TOMLDecodeError,
    ):
        return None
    return {"source": source, "version": value}


def _project_metadata(root: Path):
    metadata = {}
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            project = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {})
            if project.get("name"):
                metadata["name"] = project["name"]
            if project.get("description"):
                metadata["description"] = project["description"]
        except (OSError, tomllib.TOMLDecodeError):
            pass
    package = root / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
            metadata.setdefault("name", data.get("name"))
            metadata.setdefault("description", data.get("description"))
        except (OSError, json.JSONDecodeError):
            pass
    cargo = root / "Cargo.toml"
    if cargo.is_file():
        try:
            data = tomllib.loads(cargo.read_text(encoding="utf-8")).get("package", {})
            metadata.setdefault("name", data.get("name"))
            metadata.setdefault("description", data.get("description"))
        except (OSError, tomllib.TOMLDecodeError):
            pass
    readme = next(
        (
            root / name
            for name in ("README.md", "README.rst", "README.txt")
            if (root / name).is_file()
        ),
        None,
    )
    if not metadata.get("description") and readme:
        for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith(("#", "!", "[", "<")):
                metadata["description"] = line[:500]
                break
    metadata["name"] = metadata.get("name") or root.name
    metadata["description"] = metadata.get("description") or ""
    return metadata


def discover(root):
    """Return inferred config values, evidence, and unresolved version conflicts."""
    root = Path(root).resolve()
    metadata = _project_metadata(root)
    candidates = []
    for filename, kind, key in VERSION_FILES:
        item = _candidate(root, filename, kind, key)
        if item:
            candidates.append(item)

    conflicts = []
    if not candidates:
        canonical = {"type": "text", "file": "VERSION"}
        initial = "0.1.0"
        targets = []
        version_status = "no_existing_version_source"
    else:
        canonical = candidates[0]["source"]
        initial = candidates[0]["version"]
        if len({item["version"] for item in candidates}) > 1:
            conflicts = candidates
            version_status = "conflict"
            targets = []
        else:
            version_status = "consistent"
            targets = [item["source"] for item in candidates[1:]]

    pyproject = root / "pyproject.toml"
    pyproject_text = (
        pyproject.read_text(encoding="utf-8", errors="replace") if pyproject.is_file() else ""
    )
    python_project = (
        "[project]" in pyproject_text
        or "[tool.pytest" in pyproject_text
        or (root / "setup.py").is_file()
        or (root / "setup.cfg").is_file()
    )
    has_tests = (root / "tests").is_dir() or (root / "test").is_dir()
    has_python_build = (
        "[build-system]" in pyproject_text
        or (root / "setup.py").is_file()
        or (root / "setup.cfg").is_file()
    )
    test_commands = ["python -m pytest"] if python_project and has_tests else []
    build_commands = ["python -m build"] if has_python_build else []
    artifact_paths = ["dist/*"] if has_python_build else []

    package_json = root / "package.json"
    if package_json.is_file():
        try:
            scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
        except (OSError, json.JSONDecodeError):
            scripts = {}
        if "test" in scripts:
            test_commands.append("npm test")
        if "build" in scripts:
            build_commands.append("npm run build")
            artifact_paths.append("dist/*")

    cargo_manifest = root / "Cargo.toml"
    if cargo_manifest.is_file():
        test_commands.append("cargo test")
        build_commands.append("cargo build --release")
        artifact_paths.append("target/release/*")
    workflow_files = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    workflow_text = "\n".join(
        item.read_text(encoding="utf-8", errors="replace") for item in workflow_files
    )
    # Only recognize fixed, known commands. Never copy arbitrary workflow shell
    # commands into project configuration.
    for command in (
        "python -m pytest", "pytest", "tox", "nox",
        "npm test", "cargo test", "go test ./...",
    ):
        if command in workflow_text:
            test_commands.append(command)
    for command in (
        "python -m build", "npm run build",
        "cargo build --release", "go build ./...",
    ):
        if command in workflow_text:
            build_commands.append(command)
    test_commands = list(dict.fromkeys(test_commands))
    build_commands = list(dict.fromkeys(build_commands))
    artifact_paths = list(dict.fromkeys(artifact_paths))

    changelog = next(
        (name for name in ("CHANGELOG.md", "CHANGES.md", "HISTORY.md") if (root / name).is_file()),
        "CHANGELOG.md",
    )

    return {
        "project": metadata,
        "version": {"initial": initial, "source": canonical},
        "sync_targets": targets,
        "test_commands": test_commands,
        "build_commands": build_commands,
        "artifact_paths": artifact_paths,
        "notes_file": changelog,
        "version_status": version_status,
        "version_candidates": candidates,
        "version_conflicts": conflicts,
        "evidence": {
            "project_metadata": [
                name
                for name in (
                    "pyproject.toml", "package.json", "Cargo.toml",
                    "README.md", "README.rst", "README.txt",
                )
                if (root / name).is_file()
            ],
            "version_files": [item["source"]["file"] for item in candidates],
            "tests_detected": has_tests,
            "python_build_backend_detected": has_python_build,
            "workflow_files": [str(item.relative_to(root)) for item in workflow_files],
        },
    }


def render_config(result):
    """Render deterministic TOML using discovered values and safe policy defaults."""
    def quote(value):
        return json.dumps(str(value), ensure_ascii=False)

    project = result["project"]
    version = result["version"]
    source = version["source"]
    source_text = "{ type = " + quote(source["type"]) + ", file = " + quote(source["file"])
    if source.get("key"):
        source_text += ", key = " + quote(source["key"])
    source_text += " }"
    targets = []
    for target in result["sync_targets"]:
        item = "{ type = " + quote(target["type"]) + ", file = " + quote(target["file"])
        if target.get("key"):
            item += ", key = " + quote(target["key"])
        targets.append(item + " }")

    def array(values):
        return "[" + ", ".join(quote(value) for value in values) + "]"

    return f'''# Generated by SemVer Forge from existing project metadata.
# Review the discovery report before changing release policy.
[project]
name = {quote(project["name"])}
description = {quote(project["description"])}

[version]
initial = {quote(version["initial"])}
source = {source_text}

[git]
tag_prefix = "v"
require_clean = true
unknown_commit = "ignore"
merge_commits = "ignore"

[commits]
breaking_changes = true
ignored_types = ["docs", "style", "refactor", "test", "build", "ci", "chore"]
unknown = "ignore"

[commits.types]
feat = "minor"
fix = "patch"
perf = "patch"
revert = "patch"

[sync]
targets = [{", ".join(targets)}]

[release]
commit_version = true
annotated_tag = true
notes_file = {quote(result["notes_file"])}
require_confirmation = true
release_when_no_changes = false
test_commands = {array(result["test_commands"])}
build_commands = {array(result["build_commands"])}
artifact_paths = {array(result["artifact_paths"])}
'''
