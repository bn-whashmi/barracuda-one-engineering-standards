# Release Check Prompt

Assess whether this repository is ready to ship.

Check:

- Default branch and release branch state.
- CI/test status and known skipped checks.
- Database migrations and rollback safety.
- Feature flags and environment configuration.
- Security-sensitive changes.
- Dependency and audit alerts.
- Smoke-test coverage for user-critical paths.
- Documentation or runbook updates.

Output:

```text
Release Readiness: Ready / Blocked / Risk Accepted

Blockers
- ...

Risks
- ...

Required Verification
- ...
```
