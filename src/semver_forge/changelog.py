from __future__ import annotations

import re
from pathlib import Path

from .conventional_commits import classify, parse_message

SECTIONS = {"major": "Breaking Changes", "minor": "Features", "patch": "Fixes"}
_HASH_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])", re.IGNORECASE)


def release_notes(commits, rules=None, include_unclassified=False):
    groups = {
        "Breaking Changes": [],
        "Features": [],
        "Fixes": [],
        "Performance": [],
        "Documentation": [],
        "Maintenance": [],
        "Other Changes": [],
    }
    for c in commits:
        msg = c["message"]
        parsed = parse_message(msg)
        impact = classify(msg, rules)
        if parsed.breaking:
            section = "Breaking Changes"
        elif parsed.type == "feat":
            section = "Features"
        elif parsed.type == "fix":
            section = "Fixes"
        elif parsed.type == "perf":
            section = "Performance"
        elif parsed.type == "docs":
            section = "Documentation"
        elif parsed.type in ("chore", "build", "ci", "test", "refactor", "style"):
            section = "Maintenance"
        elif impact:
            section = SECTIONS.get(impact, "Other Changes")
        elif include_unclassified and parsed.description:
            section = "Other Changes"
        else:
            continue
        groups[section].append(f"- {parsed.description} ({c['hash'][:8]})")
    out = []
    for title, entries in groups.items():
        if entries:
            out.extend([f"### {title}", "", *entries, ""])
    return "\n".join(out).rstrip() + "\n" if out else "No release-relevant changes found.\n"


def changelog_references(text: str) -> set[str]:
    return {match.group(0).lower() for match in _HASH_RE.finditer(text)}


def _normalized_descriptions(text: str) -> set[str]:
    descriptions = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:]
        value = re.sub(r"\s+\([0-9a-f]{7,40}\)\s*$", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\[([0-9a-f]{7,40})\]\([^)]*\)", "", value, flags=re.IGNORECASE)
        value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
        if value:
            descriptions.add(value)
    return descriptions


def _commit_represented(commit: dict, references: set[str], descriptions: set[str]) -> bool:
    commit_hash = commit["hash"].lower()
    if any(commit_hash.startswith(ref) or ref.startswith(commit_hash) for ref in references):
        return True
    description = re.sub(
        r"[^a-z0-9]+", " ", parse_message(commit["message"]).description.lower()
    ).strip()
    return bool(description and description in descriptions)


def update_changelog(path, version, notes, dry_run=False):
    p = Path(path)
    existing = (
        p.read_text(encoding="utf-8")
        if p.exists()
        else "# Changelog\n\nAll notable changes to this project are documented in this file.\n"
    )
    block = f"## [{version}]\n\n{notes.strip()}\n\n"
    lines = existing.splitlines(keepends=True)
    heading = f"## [{version}]"
    matches = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == heading]
    if len(matches) > 1:
        raise ValueError(f"changelog contains duplicate headings for version {version}")
    if matches:
        start = matches[0]
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
            len(lines),
        )
        new = "".join(lines[:start]) + block + "".join(lines[end:])
    else:
        insert = 1 if lines and lines[0].startswith("#") else 0
        new = "".join(lines[:insert]) + "\n" + block + "".join(lines[insert:])
    if not dry_run:
        p.write_text(new, encoding="utf-8")
    return new


def update_unreleased(path, notes, dry_run=False):
    """Append newly discovered entries to the Unreleased section."""
    p = Path(path)
    existing = (
        p.read_text(encoding="utf-8")
        if p.exists()
        else "# Changelog\n\nAll notable changes to this project are documented in this file.\n"
    )
    if not notes or notes.strip() == "No release-relevant changes found.":
        return existing, False

    lines = existing.splitlines(keepends=True)
    heading = "## [Unreleased]"
    matches = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == heading]
    if len(matches) > 1:
        raise ValueError("changelog contains duplicate [Unreleased] headings")

    block = notes.strip() + "\n"
    if matches:
        start = matches[0]
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
            len(lines),
        )
        section = "".join(lines[start:end]).rstrip()
        new_section = section + "\n\n" + block
        new = "".join(lines[:start]) + new_section + "\n\n" + "".join(lines[end:]).lstrip("\n")
    else:
        insert = 1 if lines and lines[0].startswith("#") else 0
        unreleased = f"## [Unreleased]\n\n{block}\n"
        new = "".join(lines[:insert]) + "\n" + unreleased + "".join(lines[insert:])

    if not dry_run:
        p.write_text(new, encoding="utf-8")
    return new, new != existing


def sync_unreleased(path, commits, rules=None, dry_run=False):
    """Compare history to the changelog and append missing commit entries."""
    p = Path(path)
    existing = p.read_text(encoding="utf-8") if p.exists() else ""
    references = changelog_references(existing)
    descriptions = _normalized_descriptions(existing)
    missing = [c for c in commits if not _commit_represented(c, references, descriptions)]
    notes = release_notes(missing, rules, include_unclassified=True)
    new, changed = update_unreleased(p, notes, dry_run=dry_run)
    return {
        "path": str(p),
        "checked_commits": len(commits),
        "represented_commits": len(commits) - len(missing),
        "missing_commits": [c["hash"] for c in missing],
        "missing_count": len(missing),
        "diverged": bool(missing),
        "changed": changed and not dry_run,
        "dry_run": dry_run,
        "notes": notes,
    }
