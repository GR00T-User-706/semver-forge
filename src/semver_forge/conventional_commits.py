"""Conventional Commit parsing and release-impact classification."""
from dataclasses import dataclass
import re

HEADER = re.compile(r'^(?P<type>[A-Za-z][A-Za-z0-9-]*)(?:\((?P<scope>[^()\r\n]+)\))?(?P<bang>!)?: (?P<description>.+)$')

@dataclass(frozen=True)
class CommitMessage:
    type: str | None
    scope: str | None
    description: str
    breaking: bool
    body: str
    footers: tuple[str, ...]
    valid: bool

def parse_message(message: str) -> CommitMessage:
    lines = message.strip().splitlines()
    header = lines[0] if lines else ''
    m = HEADER.fullmatch(header)
    body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
    footers = tuple(line.strip() for line in (lines[1:] if len(lines) > 1 else []) if re.match(r'^[A-Za-z][A-Za-z -]*:\s*\S', line.strip()))
    breaking = bool(m and m.group('bang')) or any(re.match(r'^BREAKING CHANGE:\s*\S', x.strip()) for x in (lines[1:] if len(lines) > 1 else [])) or any(re.match(r'^BREAKING-CHANGE:\s*\S', x.strip()) for x in (lines[1:] if len(lines) > 1 else []))
    return CommitMessage(m.group('type').lower() if m else None, m.group('scope') if m else None, m.group('description') if m else header, breaking, body, footers, bool(m))

def classify(message: str, rules: dict | None = None) -> str | None:
    rules = rules or {}
    parsed = parse_message(message)
    if not parsed.valid:
        return None if rules.get('unknown', 'ignore') == 'ignore' else rules.get('unknown')
    if parsed.breaking and rules.get('breaking_changes', True): return 'major'
    ignored = set(rules.get('ignored_types', ['docs', 'style', 'refactor', 'test', 'build', 'ci', 'chore']))
    if parsed.type in ignored: return None
    impacts = rules.get('types', {'feat':'minor','fix':'patch','perf':'patch','revert':'patch'})
    impact = impacts.get(parsed.type)
    return impact if impact in ('major','minor','patch') else (None if rules.get('unknown', 'ignore') == 'ignore' else rules.get('unknown'))
