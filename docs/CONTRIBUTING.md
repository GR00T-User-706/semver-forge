# Contributing

Use Python 3.10+, keep the core standard-library-only, and add tests for parser, filesystem, and Git behavior. Run `./tests/run-tests.sh`. Integration tests must use temporary repositories and must not modify global Git configuration. Prefer argument arrays for subprocesses. Document unsupported behavior rather than silently guessing.
