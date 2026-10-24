# Installation

Requirements: Python 3.10 or newer and Git. No third-party runtime dependency is required.

## User-local installation

From the extracted project directory:

```sh
./scripts/install.sh --prefix "$HOME/.local"
export PATH="$HOME/.local/bin:$PATH"
export MANPATH="$HOME/.local/share/man${MANPATH:+:$MANPATH}"
semver-forge --help
man semver-forge
```

The installer installs the Python package under `PREFIX/lib/semver-forge`, the launcher under `PREFIX/bin/semver-forge`, and the man page under `PREFIX/share/man/man1/semver-forge.1`. It refuses to overwrite an existing launcher, package directory, or man page. If installation reports an existing installation, inspect it rather than deleting it blindly; an in-place upgrade command is not implemented in this version.

## Uninstall

```sh
./scripts/uninstall.sh --prefix "$HOME/.local"
```

The uninstaller validates the launcher and man-page markers before removing recognized files. Review the selected prefix first.

## Source-tree use

```sh
./bin/semver-forge --help
```

## Termux

Use the Python and Git packages available in your configured Termux repositories. A user-local prefix is supported. If `man` does not find the page automatically, set `MANPATH` to include `$HOME/.local/share/man` and `$PREFIX/share/man`.
