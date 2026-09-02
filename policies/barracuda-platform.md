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
| Kafka topic JSON Schemas | `nexus-schemas` (registered to Schema Registry on merge) |
| New service scaffold | `nexus-service-template` (GitHub template repo) |
| Public product API onboarding | `nexus-architecture/docs/onboarding-product-api.md` |
| Frontend design system rules | `nexus-ui-host/.claude/bds-guides/` and BDS skills |

See [docs/barracuda-asset-map.md](../docs/barracuda-asset-map.md) for the full
inventory.

## Commit and Branch Conventions

- Commit messages start with the Jira ticket: `NEX-{ticket} <imperative
  summary>` — e.g. `NEX-6449 Rename risk record update timestamp`. This
  replaces the conventional `type:` prefixes in the generic
  [commit-messages policy](commit-messages.md) for Nexus repositories; the
  rest of that policy (imperative voice, ≤72 chars, outcome not file list,
  no secrets) still applies.
- Branch naming: `{type}/{username}-NEX-{ticket}` where type is `feature`,
  `issue`, etc. — e.g. `feature/jsmith-NEX-1234`. Only the ticket key
  (`NEX-[0-9]+`) is machine-enforced; the branch name must contain it.
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

- Account scoping: `bcc_account_id` is the Barracuda Cloud Control account
  ID. A BCC account represents a company — either an MSP/partner account or
  a managed customer account linked under it. Every data query must scope by
  `bcc_account_id` (`BccAccountId` in C#); Kafka messages partition by it
  (per-account ordering) and database tables enforce it by foreign key.
- Authorization is hierarchical, not flat tenancy: MSP users may access
  accounts within their BCC account hierarchy (partner → managed customer
  accounts). account-service resolves the hierarchy; the mesh gateway and
  portal-service validate the requested account against it (short-TTL Redis
  cache) before routing. Access to an account outside the caller's hierarchy
  is a security violation.
- Auth boundaries — three ingress paths:
  - Browser users: OIDC/BCC IDP; the mesh gateway is the JWT validation
    boundary — backend services behind it intentionally skip full validation
    and only extract claims (see nexus-specific-patterns §6). Services
    exposed directly to the internet must perform full validation.
  - Partner telemetry producers: Auth0 client-credentials JWT, validated by
    kafka-rest-api.
  - Public API consumers: Auth0 JWT via AWS API Gateway + WAF. The
    gateway's Lambda authorizer only proves identity (signature validity
    and expiry) — the product backend must enforce the OAuth2 scope
    (`read:{slug}`, e.g. `read:barracuda_one`) and application-level
    authorization (account hierarchy, RBAC). A backend that skips scope
    checking is vulnerable even behind the gateway. New product APIs
    follow the onboarding runbook
    (`nexus-architecture/docs/onboarding-product-api.md`).
- RDS uses IAM token auth; S3 uses IAM roles; Kafka uses SASL/SSL; data at
  rest is KMS-encrypted; SOPS for committed secrets.
- Never log tokens, invite codes, session artifacts, raw customer payloads,
  or unnecessary PII.
- Bailey (the AI assistant, served by ai-service and mcp-server) is
  **read-only by design** — a documented customer-facing guarantee
  ("Working with Bailey AI Assistant", Barracuda Campus). Never expose
  write or mutation capability to the assistant; changes that do are
  high-risk and require domain-owner review.
- Organization Semgrep rules live in
  [security/semgrep/barracuda.yml](../security/semgrep/barracuda.yml);
  consuming repositories add them to their `.guardrails/semgrep-rules.yml`.

## Frontend (BDS)

- Import only from `@barracuda-internal/bds-core` — never `@mui/material`
  directly.
- Use `useTokens()` / BDS tokens for styling; never hardcode colors/spacing.
- Sentence case for all UI text.
- TanStack React Query for server state.

## New Services

- New backend services start from the `nexus-service-template` GitHub
  template ("Use this template") — CI (build, tests, coverage, PR
  validation, Jira automation), Dockerfile, OpenTelemetry/Serilog/
  Prometheus, and health endpoints come pre-wired. Do not scaffold
  services by hand.
- New public product APIs follow
  `nexus-architecture/docs/onboarding-product-api.md`: product slug,
  API Gateway base path = slug, OAuth2 scope `read:{slug}`, OpenAPI spec
  published to the shared CDN.

## Kafka and Schemas

- Topic JSON Schemas are canonical in `nexus-schemas` and are registered to
  the Confluent Schema Registry on merge. Topic and schema changes are
  high-risk and require domain-owner review.
- Producers and consumers must pass schema validation; consumer patterns
  (batching, tracing) are canonical in nexus-specific-patterns.

## Infrastructure

- Terraform: `terraform fmt`, `terraform validate`, and TFLint (org config in
  [templates/tflint.hcl](../templates/tflint.hcl)) are mandatory gates.
- Helm: all charts live in `nexus-charts`, published as OCI artifacts to ECR.
  Service charts wrap the shared `nexus-app-generic` base chart — extend it
  rather than writing raw manifests. PRs are gated by `helm lint` and a
  rendered chart-diff posted as a PR comment; chart versions are managed by
  Renovate.
- Kustomize/ArgoCD: `nexus-argocd` owns base manifests, per-environment
  overlays, and ApplicationSets. PRs are validated by `kubectl kustomize`
  builds and custom Checkov checks (`argocd-lint/`). Releases promote via
  PRs to per-environment `versions/` files (dev → qa → prod).
- Deployment ordering: infrastructure repos merge before dependent service
  repos; Kafka Schema Registry and Kafka Connect deploy before the services
  that depend on them.
- Two cluster generations coexist (legacy `-use2` and MTK3); changes to
  shared modules or overlays must account for both until legacy is retired.
- AI-generated infrastructure changes require human review regardless of AI
  review results.

## High-Risk Surfaces

Elevated scrutiny and domain-owner review for changes touching:
authentication/authorization, account isolation (BCC account hierarchy),
billing, customer data,
deployment configuration, Kafka topics or schema registry, AI assistant
capability (Bailey is read-only by design), and GraphQL schema changes
affecting authorization or backward compatibility.
