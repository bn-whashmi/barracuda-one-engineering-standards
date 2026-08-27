---
name: "docs-sync"
description: "Compare repository behavior and structure against README, AGENTS, architecture docs, setup docs, and operational docs to find and repair documentation drift. Use when a user asks to update docs, audit docs against code, improve onboarding docs, or as part of $full-test-suite."
---

# Docs Sync

Find documentation drift by comparing actual code and workflows against the repo's written guidance.

## Workflow

1. Identify the source-of-truth docs: README, AGENTS, architecture docs, setup guides, env samples, and operations notes.
2. Compare current code paths, commands, config names, and flows against those docs.
3. Promote only concrete doc drift into `project-audit-findings.md`.
4. When the correct wording is clear from repo evidence, patch docs directly if fixing is in scope.
5. Record verification as explicit reasoning when no automated test applies.

## Focus Areas

- wrong setup or build commands
- missing environment variables or permissions
- stale architecture or ownership descriptions
- outdated flow descriptions after product or API changes
- docs that tell operators to do unsafe or incomplete steps

## Rules

- Prefer exact patches over vague doc recommendations.
- Do not invent product intent; derive it from code or mark `needs-context`.

## References

- Finding format: `../_shared-project-ops/references/finding-format.md`
- Verification template: `../_shared-project-ops/references/verification-template.md`
