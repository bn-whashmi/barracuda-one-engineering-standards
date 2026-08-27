---
name: github-actions-hardening
description: "Review and harden GitHub Actions workflows for supply-chain risk, token permissions, secret handling, script injection, OIDC, reusable workflow access, and CI governance. Use when asked to audit CI/CD security, fix workflow risk, or standardize Actions across repositories."
---

# GitHub Actions Hardening

Use this skill when reviewing or changing GitHub Actions workflows.

Default policy: treat CI as an explicit repository decision. Do not add
workflow files, required GitHub Actions checks, or hosted runner dependencies
unless the repository owner has selected GitHub Actions for that repo.

## Workflow

1. Inventory `.github/workflows`, local composite actions, reusable workflows, required checks, Dependabot config, and repository Actions settings.
2. Identify trust boundaries: pull requests, forks, release jobs, deployment jobs, secrets, cloud credentials, and third-party actions.
3. Check for least-privilege `permissions`, unsafe inline scripts using untrusted context, plaintext or transformed secrets, mutable third-party action references, and long-lived cloud credentials.
4. Prefer OIDC for cloud access when the provider and deployment model support it.
5. Record concrete risks and fix the smallest safe surface first.

## Decision Rules

- Use `permissions: contents: read` as the default baseline; elevate per job only when required.
- Prefer deleting obsolete workflow files over keeping inert CI definitions.
- Treat `pull_request_target`, deployment secrets, and write tokens as high-risk until proven safe.
- Prefer full-SHA pinning for third-party actions in sensitive workflows; document any tag-based exception.
- Do not move every workflow to reusable workflows by default. Use reusable workflows only when the repo set benefits from central maintenance.
- For reusable workflows in a central repository, confirm repository Actions access policy before expecting downstream repos to call them.

## Verification

- Run workflow syntax validation where tooling exists.
- Re-read changed workflows for untrusted context interpolation.
- Confirm required checks and branch rules still reference valid workflow names.
- For deploy jobs, confirm credentials are scoped and not printed to logs.

## References

- GitHub Actions security baseline: `references/security-baseline.md`
