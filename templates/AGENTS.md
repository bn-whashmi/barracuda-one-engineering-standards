# AGENTS.md

## Project Purpose

Describe what this repository owns, who uses it, and which surfaces are
deployable.

## Repository Layout

- `apps/`: deployable applications.
- `packages/`: shared packages.
- `docs/`: product, architecture, and operational documentation.
- `.github/`: repo-local GitHub automation and templates.

Update this section to match the actual repository.

## Setup

```bash
# Add repo-specific install/setup commands here.
```

## Verification

List the narrowest useful checks first.

```bash
# Example:
# pnpm test
# pnpm build
```

## Commit Standard

Use concise, auditable commit messages starting with the Jira ticket:

```text
NEX-{ticket} <imperative summary>
```

Examples:

```text
NEX-6449 Rename risk record update timestamp
NEX-6028 Aggregate distinct risk counts in SQL instead of in-memory
NEX-6568 Fix 404 page
```

Jira automation extracts the ticket from the message via `NEX-[0-9]+`.

## Agent Rules

- Inspect the repo before making assumptions.
- Preserve unrelated local changes.
- Keep commits scoped to one coherent outcome.
- Reference the owning issue in commits or handoff notes when useful.
- Pull requests are required for default-branch changes. A single-developer
  repository may use zero required approvals; teams can raise the approval
  count as their review needs grow.
- Do not commit secrets, credentials, customer data, or private logs.
- Prefer targeted verification before broad test suites.
- Do not rewrite history or delete branches unless explicitly requested.
- Document skipped checks and the reason they were skipped.

## Security Notes

- Treat auth, permissions, billing, customer data, and deployment config as
  high-risk surfaces.
- Use `type:security` for confirmed security/privacy work.
- Never paste secrets into issue bodies, PR text, commits, or logs.

## Known Gaps

Document repo-specific validation gaps, flaky tests, missing credentials, or
deployment limitations here.
