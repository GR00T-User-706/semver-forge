# Release Payload Policy

Define what belongs in each published artifact.

## Python wheel

Include only importable runtime package files, required package data, and metadata. Exclude tests, CI workflows, local configuration, credentials, virtual environments, and unrelated repository files unless intentionally shipped as package data.

## Source distribution

Include files required to build and inspect the source release: source, build metadata, license, README, and required package data. Include tests/docs only when useful and intentional.

## Native/platform packages

For each additional format, document included files and entry points, runtime dependencies, system integration and permissions, configuration/data locations, upgrade and uninstall behavior, and validation procedure.

Inspect every artifact before publication. Never assume the build backend included or excluded a file without checking.
