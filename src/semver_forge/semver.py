"""Semantic Versioning 2.0.0 parser, precedence, and increment helpers."""
from __future__ import annotations
from dataclasses import dataclass
import re

_CORE = r'(0|[1-9]\d*)'
_PRE = r'(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
_BUILD = r'(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
_PATTERN = re.compile(rf'^{_CORE}\.{_CORE}\.{_CORE}{_PRE}{_BUILD}$')

class SemVerError(ValueError): pass

def _ids(value: str | None, prerelease: bool = False) -> tuple[str, ...]:
    if value is None: return ()
    parts = tuple(value.split('.'))
    if prerelease:
        for p in parts:
            if p.isdigit() and len(p) > 1 and p[0] == '0':
                raise SemVerError(f"numeric prerelease identifier has leading zero: {p}")
    return parts

@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> 'Version':
        if not isinstance(value, str): raise SemVerError('version must be a string')
        m = _PATTERN.fullmatch(value)
        if not m: raise SemVerError(f'invalid SemVer 2.0.0 version: {value!r}')
        major, minor, patch = map(int, m.group(1, 2, 3))
        return cls(major, minor, patch, _ids(m.group(4), True), _ids(m.group(5)))

    def __str__(self) -> str:
        core = f'{self.major}.{self.minor}.{self.patch}'
        if self.prerelease: core += '-' + '.'.join(self.prerelease)
        if self.build: core += '+' + '.'.join(self.build)
        return core

    def precedence_key(self):
        # SemVer prerelease identifiers: numeric < nonnumeric; shorter equal prefix sorts first.
        pre = (1,) if not self.prerelease else (0, tuple((0, int(x)) if x.isdigit() else (1, x) for x in self.prerelease))
        return (self.major, self.minor, self.patch, pre)

    def compare(self, other: 'Version') -> int:
        a, b = (self.major, self.minor, self.patch), (other.major, other.minor, other.patch)
        if a != b: return (a > b) - (a < b)
        if not self.prerelease and not other.prerelease: return 0
        if not self.prerelease: return 1
        if not other.prerelease: return -1
        for x, y in zip(self.prerelease, other.prerelease):
            if x == y: continue
            xn, yn = x.isdigit(), y.isdigit()
            if xn and yn: return (int(x) > int(y)) - (int(x) < int(y))
            if xn != yn: return -1 if xn else 1
            return (x > y) - (x < y)
        return (len(self.prerelease) > len(other.prerelease)) - (len(self.prerelease) < len(other.prerelease))

    def bump(self, part: str) -> 'Version':
        if part == 'major': return Version(self.major + 1, 0, 0)
        if part == 'minor': return Version(self.major, self.minor + 1, 0)
        if part == 'patch': return Version(self.major, self.minor, self.patch + 1)
        raise SemVerError(f'unsupported bump: {part}')

    def prerelease_next(self, label: str = 'alpha') -> 'Version':
        if not re.fullmatch(r'[0-9A-Za-z-]+', label) or label.isdigit(): raise SemVerError('prerelease label must be a nonnumeric SemVer identifier')
        if not self.prerelease: return Version(self.major, self.minor, self.patch, (label, '1'))
        ids = list(self.prerelease)
        if ids[0] != label: return Version(self.major, self.minor, self.patch, (label, '1'))
        if ids[-1].isdigit(): ids[-1] = str(int(ids[-1]) + 1)
        else: ids.append('1')
        return Version(self.major, self.minor, self.patch, tuple(ids))
