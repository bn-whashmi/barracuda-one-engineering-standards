# Barracuda Platform Policy

Barracuda-specific engineering requirements for the Nexus / BarracudaONE
platform, layered on top of the organization-neutral policies in this
directory. Where this document and a generic policy overlap, this document
wins for Nexus repositories.

## Canonical Sources

Do not duplicate these — they are the source of truth:

| Topic | Canonical location |
| --- | --- |
| C# coding conventions | `nexus-architecture/standards/csharp-coding-conventions.md` |
| Nexus architectural patterns (DI lifetimes, Redis keys, error propagation, Kafka, Dapr, health checks, OTel) | `nexus-architecture/standards/nexus-specific-patterns.md` |
| AI development lifecycle process | `aidlc-rules/` (v1.0.1) |
| Shared CI actions | `barracuda-internal/nexus-actions@v2` |
| Frontend design system rules | `nexus-ui-host/.claude/bds-guides/` and BDS skills |

See [docs/barracuda-asset-map.md](../docs/barracuda-asset-map.md) for the full
inventory.

## Commit and Branch Conventions

- Branch naming: `feature/{username}-NEX-{ticket}`.
- PR titles must include the Jira ticket (`NEX-xxxxx`) — enforced by
  `barracuda-internal/nexus-actions/pull-request-title-validator@v2`.
- Jira automation: PR open moves the ticket to Pending Review; merge to main
  moves it onward (ticket extracted from the commit message via
  `NEX-[0-9]+`).

## Coverage Targets

Focus enforcement on new and changed code. Repository baselines:

| Repository type | Framework | Target |
| --- | --- | --- |
| .NET backend services | xUnit + NSubstitute + Coverlet | >= 80% (via `CODE_COVERAGE_TARGET` repo variable) |
| GraphQL mesh gateway | Jest 30 + ts-jest | >= 80% |
| React frontend (nexus-ui-host) | Jest 30 + Testing Library | 100% functions and lines (hard gate) |
| Terraform | `terraform validate` + plan review | plan-based verification |

## Error Handling (Nexus)

- Production errors are masked to `"An error occurred. Please try again
  later."` (RFC 7807), except whitelisted messages (`"Invalid Session"`,
  `"Unauthenticated"`) and codes (`DEMO_ACCOUNT_OPERATION_NOT_ALLOWED`,
  `INVALID_EMAIL_FORMAT`).
- Redis and Intercom integrations are **fail-open**: catch connection and
  timeout exceptions, log a warning, return default. They must never fail a
  request. Reviewers: this is intentional, not a bug.
- Frontend: top-level `ErrorBoundary` in `App.tsx`, per-section boundaries in
  `root.tsx`.
- OpenTelemetry metric prefix `nexus_*`; health metrics `0=Healthy,
  1=Warning, 2=Critical`; Prometheus on port 9464.

## Security (Nexus)

- Tenant isolation: every tenant-scoped query must scope by `tenantId`.
- Auth: OIDC/BCC IDP; the mesh gateway is the JWT validation boundary —
  backend services intentionally skip full validation and only extract
  claims (see nexus-specific-patterns §6). Services exposed directly to the
  internet must perform full validation.
- RDS uses IAM token auth; S3 uses IAM roles; Kafka uses SASL/SSL; data at
  rest is KMS-encrypted; SOPS for committed secrets.
- Never log tokens, invite codes, session artifacts, raw customer payloads,
  or unnecessary PII.
- Organization Semgrep rules live in
  [security/semgrep/barracuda.yml](../security/semgrep/barracuda.yml);
  consuming repositories add them to their `.guardrails/semgrep-rules.yml`.

## Frontend (BDS)

- Import only from `@barracuda-internal/bds-core` — never `@mui/material`
  directly.
- Use `useTokens()` / BDS tokens for styling; never hardcode colors/spacing.
- Sentence case for all UI text.
- TanStack React Query for server state.

## Infrastructure

- Terraform: `terraform fmt`, `terraform validate`, and TFLint (org config in
  [templates/tflint.hcl](../templates/tflint.hcl)) are mandatory gates.
- Deployments are GitOps via ArgoCD kustomize updates; infrastructure repos
  merge before dependent service repos.
- AI-generated infrastructure changes require human review regardless of AI
  review results.

## High-Risk Surfaces

Elevated scrutiny and domain-owner review for changes touching:
authentication/authorization, tenant isolation, billing, customer data,
deployment configuration, Kafka topics or schema registry, and GraphQL
schema changes affecting authorization or backward compatibility.
