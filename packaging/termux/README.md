# Termux package

SemVer Forge is packaged as a normal Termux .deb. Termux's package manager
owns the installed launcher, application modules, vendored YAML dependency,
and man page. Upgrades replace the previous package-managed files.

## Build prerequisites

Install termux-create-package from its current upstream Termux package or
GitHub release. The PyPI release is stale; do not install the builder from
PyPI.

The builder itself needs Python and ruamel.yaml to parse its YAML manifest.
Install that build-time dependency in the environment running the builder:

    python -m pip install ruamel.yaml

The build script stages ruamel.yaml 0.19.1 into the package. This makes YAML
metadata discovery and synchronization work after installation without
requiring a separate pip installation on the target device. The staged
library is installed under $PREFIX/lib/semver-forge/vendor/ and its license
metadata is included in the staged distribution.

From the repository root:

    bash packaging/termux/build.sh

The helper reads the canonical VERSION file, stages the runtime dependency,
and passes the version to termux-create-package --pkg-version. Temporary
staging files are removed when the build exits. Output is written to
dist/termux/.

## Install and upgrade

    apt install ./dist/termux/semver-forge_$(cat VERSION)_all.deb

Use the same command after building a newer version. Because the package name
stays semver-forge and the package version increases, apt/dpkg treats it as
an upgrade and replaces the package-managed files.

If installing directly with dpkg:

    dpkg -i ./dist/termux/semver-forge_$(cat VERSION)_all.deb
    apt -f install

Prefer apt install ./package.deb because it resolves declared dependencies.

## Remove

    apt remove semver-forge

This removes the package-owned launcher, Python modules, vendored dependency,
and man page. It does not remove project configuration files such as
.semver-forge.toml from repositories where SemVer Forge was initialized.

## Package layout

- $PREFIX/bin/semver-forge: CLI launcher
- $PREFIX/lib/semver-forge/semver_forge/: application modules and data
- $PREFIX/lib/semver-forge/vendor/: package-owned ruamel.yaml runtime dependency
- $PREFIX/share/man/man1/semver-forge.1: manual page

The package is architecture-independent (all): it installs Python source
files and does not compile native extensions.

## Maintainer scripts

No preinst dependency installer is used. Required system packages are
declared in the package control metadata so APT resolves them before
installation. Python runtime code dependencies are included as package-owned
files rather than installed with pip from a maintainer script.
