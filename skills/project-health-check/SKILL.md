---
name: "project-health-check"
description: "Assess a repository's overall engineering health by inspecting repo structure, CI or test status, stale docs, risky config drift, TODO hotspots, maintenance hazards, and operational friction. Use when a user asks for a project health review, maintenance audit, cleanup roadmap, repo triage, or as part of $full-test-suite."
---

# Project Health Check

Review the repository for broad engineering health risks and promote only evidence-backed findings.

## Quick Start

1. Confirm repo root, branch, dirty worktree, and available tools.
2. Inspect manifests, CI files, docs, TODO or FIXME hotspots, ignored files, environment samples, and high-churn paths.
3. Record confirmed findings in `project-audit-findings.md` using `../_shared-project-ops/references/finding-format.md`.
4. Use `../_shared-project-ops/references/severity-rubric.md` for prioritization.
5. If GitHub issue sync is in scope, let `$issue-operator` handle issue lifecycle.

## Focus Areas

- broken or absent checks for important surfaces
- stale architecture, setup, or operational docs
- risky config drift between local, CI, and sample env files
- ownership gaps, abandoned modules, or high-churn hotspots
- TODO, FIXME, HACK, or silent fallback clusters that hide real risk
- generated artifacts or caches tracked in ways that create operational noise

## Promotion Rules

- Do not log mere style preferences.
- Promote a finding only when you can show a concrete maintenance, release, or reliability risk.
- Use `blocked` or `needs-context` when repo evidence is incomplete.

## Outputs

- Update `project-audit-findings.md`.
- When useful, summarize repo health and candidate cleanup order.

## References

- Finding format: `../_shared-project-ops/references/finding-format.md`
- Severity rubric: `../_shared-project-ops/references/severity-rubric.md`
- Dedupe rules: `../_shared-project-ops/references/dedupe-rules.md`
