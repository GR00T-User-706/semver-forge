#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$ROOT"

BUILDER="$(command -v termux-create-package || true)"
[[ -n "$BUILDER" ]] || {
    printf "%s\n" "error: termux-create-package is not installed" >&2
    exit 127
}

command -v python >/dev/null 2>&1 || {
    printf "%s\n" "error: Python is required to build the Termux package" >&2
    exit 127
}

# termux-create-package parses its YAML manifest with ruamel.yaml.
python -c 'from ruamel.yaml import YAML; YAML()' 2>/dev/null || {
    printf "%s\n" "error: the build environment is missing ruamel.yaml" >&2
    printf "%s\n" "install the builder dependency with: python -m pip install ruamel.yaml" >&2
    exit 1
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

BUILD_DIR="packaging/termux/.build"
VENDOR_DIR="$BUILD_DIR/vendor"
if [[ -e "$BUILD_DIR" ]]; then
    printf "error: build staging directory already exists: %s\n" "$BUILD_DIR" >&2
    printf "%s\n" "inspect it and remove it manually before rebuilding" >&2
    exit 1
fi

mkdir -p "$VENDOR_DIR"
cleanup() {
    rm -rf -- "$BUILD_DIR"
}
trap cleanup EXIT

# ruamel.yaml 0.19.1 is pure Python and no longer needs its optional C extension.
python -m pip install \
    --disable-pip-version-check \
    --no-compile \
    --no-deps \
    --target "$VENDOR_DIR" \
    "ruamel.yaml==0.19.1"

PYTHONPATH="$VENDOR_DIR${PYTHONPATH:+:$PYTHONPATH}" python -c \
    'from ruamel.yaml import YAML; YAML(typ="rt"); print("ruamel.yaml runtime staging: OK")'

mkdir -p dist/termux
"$BUILDER" --pkg-version "$VERSION_VALUE" packaging/termux/semver-forge.yaml

PACKAGE="dist/termux/semver-forge_${VERSION_VALUE}_all.deb"
[[ -s "$PACKAGE" ]] || {
    printf "error: package builder did not create expected artifact: %s\n" "$PACKAGE" >&2
    exit 1
}

printf "\nBuilt package: %s\n" "$PACKAGE"
