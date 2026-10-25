#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$ROOT"

command -v termux-create-package >/dev/null 2>&1 || {
    printf "%s\n" "error: termux-create-package is not installed" >&2
    exit 127
}

[[ -f VERSION ]] || {
    printf "%s\n" "error: VERSION file is missing" >&2
    exit 1
}

VERSION_VALUE="$(<VERSION)"
[[ "$VERSION_VALUE" =~ ^[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$ ]] || {
    printf "error: VERSION is not a supported package version: %s\n" "$VERSION_VALUE" >&2
    exit 1
}

mkdir -p dist/termux
termux-create-package \
    --pkg-version "$VERSION_VALUE" \
    packaging/termux/semver-forge.yaml

printf "\nBuilt package: %s\n" "dist/termux/semver-forge_${VERSION_VALUE}_all.deb"
