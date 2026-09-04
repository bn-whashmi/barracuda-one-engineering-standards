<!--
Master copy: barracuda-one-engineering-standards/templates/copilot-instructions.md
Copy into your repo as .github/copilot-instructions.md. Keep it short —
Copilot follows a tight list better than an essay. Add repo-specific lines
under "Repo specifics" at the bottom; do not remove the platform sections.
-->

# Barracuda Nexus — Copilot Instructions

You are reviewing or writing code for the Nexus / BarracudaONE platform
(multi-tenant MSP security management). Follow these rules.

## Intentional platform patterns — do NOT flag these as bugs

- Fail-open Redis and Intercom: catching connection/timeout exceptions,
  logging a warning, and returning null/default is the required pattern.
  It must never fail a request.
- Production error masking: generic error copy ("An error occurred...")
  with a small whitelist ("Invalid Session", "Unauthenticated",
  DEMO_ACCOUNT_OPERATION_NOT_ALLOWED, INVALID_EMAIL_FORMAT) is by design
  (RFC 7807).
- Gateway-delegated JWT validation: backend services behind the GraphQL
  mesh gateway intentionally skip issuer/audience/lifetime validation and
  only extract claims. Flag missing validation only on services exposed
  directly to the internet.
- MSP account-hierarchy traversal: MSP users legitimately access their
  managed customer accounts. Cross-account access inside the caller's BCC
  account hierarchy is correct behavior.

## Always flag these

- Any query touching account data that is not filtered by `bcc_account_id`
  (`BccAccountId` in C#), or access to an account outside the caller's
  authorized BCC account hierarchy.
- `@mui/material` imports — only `@barracuda-internal/bds-core` is
  allowed. Hardcoded colors/spacing instead of `useTokens()`.
- SQL built from string concatenation or interpolation — require
  parameterized queries.
- Tokens, invite codes, session artifacts, raw customer payloads, or PII
  in logs or error messages.
- Disabled TLS/certificate validation outside test fixtures.
- Any change giving the Bailey AI assistant (ai-service, mcp-server)
  write or mutation capability — Bailey is read-only by design (a
  documented customer guarantee).
- Blocking calls on async paths (`.Result`, `.Wait()`); missing
  `ConfigureAwait(false)` on library async paths (.NET).
- New or changed behavior without tests; bug fixes without a regression
  test.

## Conventions

- Commits: `NEX-{ticket} <imperative summary>` (e.g. `NEX-6449 Rename
  risk record update timestamp`). Branches contain the ticket key.
- .NET: PascalCase, DI via `AddService()` extension methods, OpenTelemetry
  metrics prefixed `nexus_*`, health values 0=Healthy 1=Warning 2=Critical,
  Redis keys `{service}:{entity}:{identifier}`.
- TypeScript/React: ESLint + Prettier, strict TS, TanStack React Query for
  server state, sentence case for UI text.
- GraphQL schema changes must preserve backward compatibility unless the
  PR explicitly says otherwise.
- Keep PRs to one concern; suggest splitting oversized or multi-concern
  changes.

## High-risk changes — recommend human domain-owner review

Authentication/authorization, account isolation (BCC hierarchy), billing,
customer data handling, deployment configuration (Terraform/Helm/ArgoCD),
Kafka topics or schema registry, AI assistant capability, and GraphQL
authorization changes.

## Where details live

- This repo's specifics: `CLAUDE.md` (and `AGENTS.md` if present).
- Platform standards: the `barracuda-one-engineering-standards` repo
  (policies/barracuda-platform.md, pr-review/barracuda-context.md).

## Repo specifics

<!-- Add 2-5 repo-specific rules here (key commands, local patterns). -->
