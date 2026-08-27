---
name: "release-readiness"
description: "Review whether a repository is ready to ship by checking versioning, changelog, feature flags, migrations, rollout safety, smoke-test coverage, and operational readiness. Use when a user asks for release readiness, ship checks, launch gating, or as part of $full-test-suite pre-release work."
---

# Release Readiness

Assess whether the current repo state is safe to release.

## Focus Areas

- versioning and changelog completeness
- migration and backward-compatibility risk
- feature-flag defaults and rollback path
- required env vars, secrets, and deployment assumptions
- smoke tests or targeted verifications for changed flows

## Rules

- Promote only concrete release blockers or release risks.
- Record findings in `project-audit-findings.md`.

## References

- Finding format: `../_shared-project-ops/references/finding-format.md`
- Severity rubric: `../_shared-project-ops/references/severity-rubric.md`
