# Barracuda Review Context

Platform context for all four AI review lenses when reviewing Nexus /
BarracudaONE repositories. Read together with the generic guides in this
directory.

## Intentional Patterns — Do Not Flag as Bugs

- **Fail-open Redis and Intercom**: catching connection/timeout exceptions,
  logging a warning, and returning default is the required pattern.
- **Production error masking**: generic error copy with a small whitelist
  (`"Invalid Session"`, `"Unauthenticated"`, `DEMO_ACCOUNT_OPERATION_NOT_ALLOWED`,
  `INVALID_EMAIL_FORMAT`) is by design (RFC 7807).
- **Gateway-delegated JWT validation**: backend services behind the mesh
  gateway intentionally disable issuer/audience/lifetime validation; the
  gateway is the auth boundary. Flag it only on services exposed directly to
  the internet (e.g. entraid-service endpoints, which must validate fully).

## Platform-Specific Checks

Engineering:
- `ConfigureAwait(false)` on library async paths; never `.Result`/`.Wait()`.
- DI lifetimes per nexus-specific-patterns §1 (singleton for token-caching,
  scoped for per-request business logic).
- Redis keys follow `{service}:{entity}:{identifier}`.
- OTel metrics use the `nexus_*` prefix; health values 0/1/2.
- BDS imports only from `@barracuda-internal/bds-core`.
- GraphQL schema changes preserve backward compatibility unless authorized.

Security:
- Every data query scopes by `bcc_account_id` (`BccAccountId` in C#) — the
  BCC (Barracuda Cloud Control) account ID identifying a company. Unscoped
  queries, or access to an account outside the caller's authorized BCC
  account hierarchy, are P0. Hierarchy traversal by MSP users over their
  managed customer accounts is legitimate by design — do not flag it.
  Kafka messages partition by `bcc_account_id`; account-service resolves
  the hierarchy and the mesh gateway validates the requested account
  against it (short-TTL Redis cache) before routing — backend services
  must still never run an unscoped account-data query.
- Three auth boundaries: BCC IDP OIDC for browser traffic through the mesh
  gateway; Auth0 client-credentials JWT at kafka-rest-api for partner
  telemetry; Auth0 via API Gateway + WAF + Lambda authorizer for public API
  consumers. Changes on any of the three are high-risk.
- RDS via IAM tokens, S3 via IAM roles, Kafka via SASL/SSL, KMS at rest.
- No tokens, invite codes, session artifacts, or raw customer payloads in
  logs or AI prompts.
- Bailey (ai-service, mcp-server) is read-only by design — a documented
  customer guarantee. Any change exposing write or mutation capability to
  the assistant is P0 unless explicitly authorized.
- FIDO MFA and Entra ID integration changes are high-risk. Entra ID
  behavior is customer-documented: 12-hour auto sync and published
  identity risk checks (weak/absent MFA, phishing-resistant MFA not
  enforced, unmanaged device access, excessive global admins) — changes
  to risk-detection logic or sync cadence are customer-visible.

QA:
- Coverage: 80% for .NET/gateway, 100% functions+lines for nexus-ui-host.
- Fail-open paths need both cache-hit and cache-miss tests.
- Frontend tests colocated in `unit-tests/` directories.
- Backend API changes: platform-level API E2E tests live in
  `nexus-playwright` (live dev/QA GraphQL + REST suites with DB-seeding
  factories). Flag new or changed endpoints with no coverage there.

Repo standards:
- Canonical ground truth: `nexus-architecture/standards/` and each repo's
  `CLAUDE.md`/`AGENTS.md`. Report missing docs as a gap, never invent rules.

## High-Risk Surfaces (Escalate to Domain Owner)

Authentication/authorization, account isolation (BCC account hierarchy),
billing, customer data,
deployment configuration (Terraform/Helm/ArgoCD), Kafka topics and schema
registry, AI assistant capability (Bailey read-only guarantee), and
GraphQL authorization changes.
