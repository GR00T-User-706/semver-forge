# Conventional Commits

Header format: `type(scope)!: description`; scope and `!` are optional. A body and footers may follow. Breaking changes are detected from `!`, `BREAKING CHANGE:`, or `BREAKING-CHANGE:`. Default mapping: feat=minor; fix=patch; perf=patch; breaking=major. Default ignored types: docs, style, refactor, test, build, ci, chore. Unknown messages are ignored. The highest impact in the range wins.

`0.y.z` is pre-1.0 software: SemVer convention treats the public API as unstable. This tool still follows the configured mapping literally; a breaking change increments major from `0.x.y` to `1.0.0`, which is a practical policy choice rather than a special SemVer rule. Configure policies explicitly if you prefer breaking changes to remain within `0.y.z`.
