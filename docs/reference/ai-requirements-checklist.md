# AI Code-Generation Requirements Checklist

Generic questions to answer **before** asking an AI tool to generate a
feature for a Nexus / BarracudaONE repository, and to verify against before
merging the result. Use the sections that apply; skip the rest. This is an
org standard — keep feature- and ticket-specific requirement documents in
Jira or the owning repository, never here.

## Functional

- What is the core behavior, and what are the explicit non-goals?
- What are the edge cases, validation rules, and error states?
- What loading, empty, and zero-data states exist in the UI?
- What accessibility and responsive requirements apply?

## Data

- Which service owns the data? Which database entities and migrations change?
- Does the GraphQL schema change, and is it backward compatible?
- Are Kafka topics or schema-registry entries affected? Who approves them?
- How is data cached (Redis key pattern per `{service}:{entity}:{identifier}`),
  and what is the invalidation story?

## Non-Functional

- Expected data volumes and pagination strategy?
- Sync vs async processing; timeouts; retry and fallback behavior?
- What gets logged (structured, correlation ID, no PII/tokens), what metrics
  (`nexus_*` prefix), what alerts?

## Security and Tenancy

- How is the endpoint authenticated and authorized (gateway-delegated JWT vs
  direct validation)?
- Is every account-scoped query filtered by `bcc_account_id`
  (`BccAccountId`), and is access authorized against the caller's BCC
  account hierarchy?
- For MSP scenarios: what is aggregated across managed customer accounts vs
  per-account, and what happens when a customer is removed from MSP
  management?
- Any input that reaches SQL, shell, or a template — is it parameterized?

## Frontend

- Which BDS components and tokens apply? (No direct `@mui/material` imports.)
- Is there a design source (Figma/prototype) to verify against?
- Light/dark theme behavior covered?

## Testing

- Unit tests with meaningful assertions for new/changed behavior?
- Failure-path tests (including fail-open cache-miss paths)?
- Coverage meets the repo threshold (80% .NET/gateway, 100% nexus-ui-host)?
- Integration/e2e coverage where unit tests cannot establish behavior?

## Deployment

- Feature flag (Split.io) or hard rollout? Rollback path?
- Database migration ordering across repos?
- Monitoring in place before enablement?

## Common Pitfalls to Verify Against

- N+1 queries and over-fetching in GraphQL resolvers.
- PII, tokens, or raw payloads in logs.
- Silent catch blocks on stateful paths.
- Hardcoded strings that should be constants or i18n messages.
- New dependencies without license/vulnerability review.
- TODOs without a tracking ticket.
