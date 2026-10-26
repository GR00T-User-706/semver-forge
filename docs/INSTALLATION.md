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

## Uninstall

```sh
./scripts/uninstall.sh --prefix "$HOME/.local"
```

## Source-tree use

```sh
./bin/semver-forge --help
```

## Termux

Use the Python and Git packages available in your configured Termux repositories. For the Termux package workflow, see `packaging/termux/README.md`.
