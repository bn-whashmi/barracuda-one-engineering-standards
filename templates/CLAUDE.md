# CLAUDE.md

<!-- Barracuda Nexus repository configuration for Claude Code.
     Copy this template and fill in every section — an unedited template
     misleads AI reviewers. -->

## Project Overview

<!-- What this repository owns, who uses it, deployable surfaces. -->

## Key Technologies

<!-- e.g. .NET 10, ASP.NET Core, EF Core / TypeScript, Node 24, React 18 /
     Terraform. PostgreSQL (RDS IAM), Redis, Kafka (MSK), Dapr. -->

## Canonical Standards

- C# conventions: `nexus-architecture/standards/csharp-coding-conventions.md`
- Platform patterns: `nexus-architecture/standards/nexus-specific-patterns.md`
- Org policy: `barracuda-one-engineering-standards/policies/barracuda-platform.md`

## Commands

```bash
# Build:   dotnet build --no-restore        | yarn build
# Test:    dotnet test                      | yarn test:unit
# Format:  dotnet format --verify-no-changes| yarn lint:prettier
# Lint:    (C# analyzers via build)         | yarn lint:eslint && yarn lint:typescript
```

Do not commit if any check fails.

## Conventions

<!-- Naming, file organization, coverage threshold (80% .NET / 100%
     nexus-ui-host), colocated unit-tests/ dirs, BDS-only imports, etc. -->

## Intentional Platform Patterns

- Fail-open Redis and Intercom (never throw on cache/integration failure).
- Production error masking (RFC 7807, whitelisted messages only).
- JWT validation delegated to the mesh gateway (backends extract claims only).

## CI/CD

- Branch: `{type}/{username}-NEX-{ticket}` (e.g. `feature/jsmith-NEX-1234`);
  the branch name must contain the ticket key, and the PR title must include
  NEX-xxxxx.
- GitHub Actions with `barracuda-internal/nexus-actions@v2`; ArgoCD GitOps.
- Jira transitions are automated on PR open and merge.

## Security

- Account scoping: scope every account-data query by `bcc_account_id`
  (`BccAccountId`); authorization follows the BCC account hierarchy
  (MSP partner → managed customer accounts).
- Never commit or log secrets, tokens, customer data, or PII.
- IAM auth for RDS/S3; SASL/SSL for Kafka; KMS at rest.
