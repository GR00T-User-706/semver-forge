from pathlib import Path

from .conventional_commits import classify, parse_message

SECTIONS = {"major": "Breaking Changes", "minor": "Features", "patch": "Fixes"}


def release_notes(commits, rules=None):
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
        else:
            continue
        groups[section].append(f"- {parsed.description} ({c['hash'][:8]})")
    out = []
    for title, entries in groups.items():
        if entries:
            out.extend([f"### {title}", "", *entries, ""])
    return "\n".join(out).rstrip() + "\n" if out else "No release-relevant changes found.\n"


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
