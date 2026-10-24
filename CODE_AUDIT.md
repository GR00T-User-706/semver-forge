# Code Audit Policy

Code audits are evidence-driven reviews of correctness, security, maintainability, packaging, and project consistency.

## Scope

Define scope before inspection. Identify active source, tests, build configuration, dependencies, workflows, and relevant documentation. Respect project-specific exclusions such as generated, vendored, archived, or fixture data.

## Read-only first pass

The initial audit is read-only. Do not modify files, install dependencies, alter configuration, run auto-fixers, or create commits during the initial pass.

## Review areas

- Runtime correctness and error handling.
- Input validation and trust boundaries.
- Authentication, authorization, secrets, and sensitive logging.
- Filesystem and subprocess safety.
- Dependency and build-system integrity.
- Public API and backward compatibility.
- Test coverage and CI behavior.
- Version and changelog consistency.
- Documentation accuracy.
- Dead, incomplete, or unreachable functionality.

## Evidence standards

Every finding must identify its location, evidence, impact, and reproduction where possible. Separate confirmed defects from suspicions and recommendations. Do not report a missing feature as a defect unless requirements or documented behavior establish that it should exist.

## Severity

- **Critical:** likely severe compromise, data loss, or system-wide failure.
- **High:** serious security or functional impact with realistic conditions.
- **Medium:** meaningful defect or risk with limited scope or prerequisites.
- **Low:** minor defect, edge case, or maintainability concern.
- **Informational:** observation or improvement suggestion without demonstrated defect.

## Remediation

An audit does not automatically authorize remediation. Report findings first. Obtain approval before broad changes, destructive operations, dependency replacement, architecture changes, or work with material compatibility impact.

Use `docs/CODE_AUDIT.md` for the report format.
