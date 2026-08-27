# Dependency Remediation Workflow

Use this workflow for Dependabot, Snyk, npm audit, and package upgrade work.

## Inspect

- Current alerts and severity.
- Package manager and lockfile.
- Runtime version.
- CI/build/test commands.
- Whether the dependency is direct or transitive.

## Fix

- Prefer direct upgrades when available.
- Use overrides only when the vulnerable package is transitive and no parent
  upgrade is available.
- Keep package manifests consistent with repository visibility, publishability, and the selected license.
- Avoid unrelated dependency churn unless the task is a broad upgrade.

## Verify

- Install with lockfile consistency.
- Run focused tests for affected package paths.
- Run build/typecheck where practical.
- Re-run audit or alert check.
- Document residual alerts and why they remain.
