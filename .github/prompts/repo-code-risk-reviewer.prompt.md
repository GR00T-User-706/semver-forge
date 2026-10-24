# Read-only Python repository risk review

Review the current repository using `AGENTS.md` and `docs/CODE_AUDIT.md`.

First inspect repository structure, project metadata, dependencies, source, tests, CI, packaging configuration, version sources, and relevant documentation. Do not modify files, install dependencies, run auto-fixers, or create commits.

Prioritize concrete correctness, security, packaging, dependency, and regression risks. Trace data from inputs to sensitive operations. Check filesystem access, subprocess usage, deserialization, network boundaries, secrets, error handling, and public API compatibility.

For every finding provide severity, confidence/status, exact file and line/function, direct evidence, realistic impact and prerequisites, reproduction steps if confirmed, smallest responsible remediation, and suggested regression test.

Separate confirmed defects from inferred risks and improvement suggestions. Do not report speculative issues as confirmed. Finish with checks actually run, areas not inspected, and decisions requiring maintainer approval.
