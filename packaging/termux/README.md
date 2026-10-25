# Termux package

SemVer Forge is packaged as a normal Termux .deb. Termux's package manager
owns the installed files, so upgrades replace the previous package version
instead of colliding with a hand-managed user-local installation.

## Build

Install termux-create-package from its current upstream GitHub release.
The PyPI release is stale; use the upstream installation instructions.

From the repository root:

```sh
./packaging/termux/build.sh
```

The helper reads the canonical VERSION file and passes that value to
termux-create-package --pkg-version. The manifest Version field is a fallback.
Output is written to dist/termux/.

## Install and upgrade

```sh
apt install ./dist/termux/semver-forge_$(cat VERSION)_all.deb
```

Use the same command after building a newer version. Because the package name
stays semver-forge and the package version increases, apt/dpkg treats it as
an upgrade and replaces the package-managed files.

If installing directly with dpkg:

```sh
dpkg -i ./dist/termux/semver-forge_$(cat VERSION)_all.deb
apt -f install
```

Prefer apt install ./package.deb because it resolves dependencies.

## Remove

```sh
apt remove semver-forge
```

This removes the package-owned launcher, Python modules, and man page. It
does not remove project configuration files such as .semver-forge.toml from
repositories where SemVer Forge was initialized.

## Package layout

- $PREFIX/bin/semver-forge: CLI launcher
- $PREFIX/lib/semver-forge/semver_forge/: application modules and data
- $PREFIX/share/man/man1/semver-forge.1: manual page

The package is architecture-independent (all): it installs Python source
files and does not compile native extensions.
