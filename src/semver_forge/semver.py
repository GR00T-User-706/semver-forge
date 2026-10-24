"""Semantic Versioning 2.0.0 parser, precedence, and increment helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

_CORE = r"(0|[1-9]\d*)"
_PRE = r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
_BUILD = r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
_PATTERN = re.compile(rf"^{_CORE}\.{_CORE}\.{_CORE}{_PRE}{_BUILD}$")


class SemVerError(ValueError):
    pass


def _ids(value: str | None, prerelease: bool = False) -> tuple[str, ...]:
    if value is None:
        return ()
    parts = tuple(value.split("."))
    if prerelease:
        for part in parts:
            if part.isdigit() and len(part) > 1 and part[0] == "0":
                raise SemVerError(
                    f"numeric prerelease identifier has leading zero: {part}"
                )
    return parts


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> Version:
        if not isinstance(value, str):
            raise SemVerError("version must be a string")
        match = _PATTERN.fullmatch(value)
        if not match:
            raise SemVerError(f"invalid SemVer 2.0.0 version: {value!r}")
        major, minor, patch = map(int, match.group(1, 2, 3))
        return cls(
            major,
            minor,
            patch,
            _ids(match.group(4), True),
            _ids(match.group(5)),
        )

    def __str__(self) -> str:
        core = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            core += "-" + ".".join(self.prerelease)
        if self.build:
            core += "+" + ".".join(self.build)
        return core

    def precedence_key(self):
        # SemVer prerelease identifiers: numeric < nonnumeric; shorter equal prefix sorts first.
        pre = (
            (1,)
            if not self.prerelease
            else (
                0,
                tuple(
                    (0, int(value)) if value.isdigit() else (1, value)
                    for value in self.prerelease
                ),
            )
        )
        return (self.major, self.minor, self.patch, pre)

    def compare(self, other: Version) -> int:
        current = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)
        if current != other_core:
            return (current > other_core) - (current < other_core)
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        for left, right in zip(self.prerelease, other.prerelease, strict=False):
            if left == right:
                continue
            left_numeric, right_numeric = left.isdigit(), right.isdigit()
            if left_numeric and right_numeric:
                return (int(left) > int(right)) - (int(left) < int(right))
            if left_numeric != right_numeric:
                return -1 if left_numeric else 1
            return (left > right) - (left < right)
        return (len(self.prerelease) > len(other.prerelease)) - (
            len(self.prerelease) < len(other.prerelease)
        )

    def bump(self, part: str) -> Version:
        if part == "major":
            return Version(self.major + 1, 0, 0)
        if part == "minor":
            return Version(self.major, self.minor + 1, 0)
        if part == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        raise SemVerError(f"unsupported bump: {part}")

    def prerelease_next(self, label: str = "alpha") -> Version:
        if not re.fullmatch(r"[0-9A-Za-z-]+", label) or label.isdigit():
            raise SemVerError(
                "prerelease label must be a nonnumeric SemVer identifier"
            )
        if not self.prerelease:
            return Version(self.major, self.minor, self.patch, (label, "1"))
        identifiers = list(self.prerelease)
        if identifiers[0] != label:
            return Version(self.major, self.minor, self.patch, (label, "1"))
        if identifiers[-1].isdigit():
            identifiers[-1] = str(int(identifiers[-1]) + 1)
        else:
            identifiers.append("1")
        return Version(
            self.major,
            self.minor,
            self.patch,
            tuple(identifiers),
        )
