---
name: "bug-hunter"
description: "Find evidence-backed correctness bugs by tracing failing tests, crash reports, suspicious control flow, unsafe edge-case handling, regressions, decode mismatches, and broken user flows. Use when a user asks to find bugs, investigate regressions, review a changed area for defects, or as part of $full-test-suite."
---

# Bug Hunter

Hunt for real, verifiable correctness bugs and fix candidates. Stay repo-grounded and evidence-first.

## Workflow

1. Identify the target surface from changed files, failing tests, logs, traces, or user-reported flows.
2. Inspect control flow, validation, serialization, concurrency, lifecycle handling, error paths, and state transitions.
3. Prefer a minimal repro, targeted test, or strong static proof before promoting a finding.
4. Log confirmed findings in `project-audit-findings.md`.
5. If fixing is in scope, fix one confirmed bug at a time and record verification evidence.

## Common Targets

- off-by-one or nil-path bugs
- state desynchronization and persistence errors
- decode or schema mismatches
- stale caches and partial update bugs
- race conditions, retry loops, cancellation, or lifecycle misuse
- regression risks from refactors or fallback logic

## Rules

- Do not create findings for speculative smells.
- Prefer tests or reproductions over broad assertions.
- Keep fix diffs small and reversible.

## References

- Finding format: `../_shared-project-ops/references/finding-format.md`
- Verification template: `../_shared-project-ops/references/verification-template.md`
- Rerun policy: `../_shared-project-ops/references/rerun-policy.md`
