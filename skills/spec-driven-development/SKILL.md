---
name: spec-driven-development
description: "Use Spec Kit with the engineering standards preset for substantial feature work, cross-client changes, unclear requirements, or risky refactors that need durable specs, plans, tasks, and release evidence."
---

# Spec-Driven Development

Use this skill when a repository should use Spec Kit before implementation.

## Workflow

1. Confirm the change fits Spec Kit: substantial feature, cross-client work,
   unclear requirements, architecture-sensitive change, or risky refactor.
2. Confirm the repository is initialized with Spec Kit and has the engineering
   standards preset installed.
3. Use `$speckit-constitution` when governing principles are missing or stale.
4. Use `$speckit-specify` to produce the feature spec.
5. Use `$speckit-clarify` if the spec contains high-impact ambiguities.
6. Use `$speckit-plan` to produce the technical implementation plan.
7. Use `$speckit-tasks` to generate implementation tasks.
8. Use `$speckit-analyze` before implementation when artifacts might drift.
9. Use `$speckit-implement` only after spec, plan, and tasks are coherent.

## Install Commands

From a Spec Kit initialized repository:

```bash
specify preset add --dev /path/to/engineering-standards/tooling/speckit/engineering-standards --priority 5
specify preset list
specify preset resolve spec-template
```

For a packaged release, publish the ZIP to an HTTPS release URL:

```bash
specify preset add --from https://github.com/engineering-standards/spec-kit-preset-engineering-standards/releases/download/v1.0.0/spec-kit-preset-engineering-standards-v1.0.0.zip --priority 5
```

## Standards

- Keep `spec.md` free of implementation details.
- Keep technical decisions in `plan.md`.
- Keep tasks grouped by independently testable user story.
- Link the owning issue or tracker when one exists.
- Include parity and contract checks for multi-surface behavior.
- Include release evidence for production-facing changes.
- Never store secrets, tokens, customer data, private logs, or sensitive
  operational details in Spec Kit artifacts.

## Verification

- `specify preset list`
- `specify preset resolve spec-template`
- `python3 tooling/validate-skills.py` in this standards repository
