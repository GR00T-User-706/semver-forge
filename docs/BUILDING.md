# Building and Packaging

Building the project is separate from calculating and tagging its release.

SemVer Forge does not invoke build commands, run test suites, inspect build artifacts, or publish packages. Use the project's own build instructions and CI pipeline. For Python projects using PEP 517, a common build frontend is:

```sh
python -m pip install build
python -m build
```

Inspect artifacts with the tools appropriate to the package format. For Python distributions, for example:

```sh
python -m pip install twine
python -m twine check dist/*
```

Native OS packages, containers, standalone executables, and language-specific bundles belong to the project's packaging workflow or PKGforge. Document each supported target, build host, prerequisites, exact commands, output paths, and validation procedure.

Use SemVer Forge separately to calculate and synchronize the version and create the local Git release tag.
