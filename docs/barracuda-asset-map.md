# Barracuda Asset Map

Existing platform assets this standards repo builds on. These are canonical —
reference them, do not fork their content into this repo.

## Standards Content

| Asset | Location | What it is |
| --- | --- | --- |
| C# coding conventions | `nexus-architecture/standards/csharp-coding-conventions.md` | 745 lines: naming, formatting, async, XML docs, 18 documented deviations from Microsoft defaults |
| Nexus architectural patterns | `nexus-architecture/standards/nexus-specific-patterns.md` | 757 lines: DI lifetimes, Redis key naming, error propagation, Kafka, Dapr, health checks, OTel, GraphQL, advisory locks |
| Convention audit methodology | `nexus-architecture/repo-auditing/` | Scored baseline audits per repo, strict-vs-guideline enforcement split, AI-compliance pilot results |
| AI development lifecycle | `aidlc-rules/` (v1.0.1, 32 files) | Full adaptive AI-DLC: inception/construction phases, security baselines, content validation, audit logging |
| AI requirements checklist | [reference/ai-requirements-checklist.md](reference/ai-requirements-checklist.md) | Generic pre-generation and pre-merge questionnaire: functional, NFR, tenancy, testing, pitfalls (distilled from platform practice; feature-specific requirement docs stay in Jira) |
| BDS conventions + skills | `nexus-ui-host/.claude/bds-guides/`, `.claude/skills/` | Design-system rules, anti-patterns, compliance-check skills, token references |
| Customer-facing behavior guarantees | Barracuda Campus, BarracudaONE space (`documentation.campus.barracuda.com/wiki/spaces/ONE`) | Documented product behavior code must not silently change: Bailey read-only guarantee, Entra ID 12-hour sync + published identity risks, API portal scope model |
| New service scaffold | `nexus-service-template` (GitHub template repo) | Pre-wired .NET service: CI (build/test/coverage, PR validator, Jira automation), Dockerfile, OpenTelemetry/Serilog/Prometheus, health endpoints, opt-in HotChocolate + EF Core/IAM examples |
| Product API onboarding runbook | `nexus-architecture/docs/onboarding-product-api.md` | Slug/base-path/`read:{slug}` scope conventions, gateway-proves-identity vs backend-proves-authorization trust split, OpenAPI publication to shared CDN |
| Platform API E2E tests | `nexus-playwright` | Live dev/QA GraphQL + REST test suites with DB-seeding factories and auto-cleanup; runs in CI via the `run-b1-tests` Docker image |
| Agent workflow skills | `nexus-architecture/.claude/skills/` | Jira ticket lifecycle (create/complete/verify), doc-sync CI, and repo-audit skills |

## CI/CD Assets

| Asset | Location | Notes |
| --- | --- | --- |
| Shared CI actions | `barracuda-internal/nexus-actions@v2` | PR title/checklist validators (`jira_projects: NEX`), Jira transitions, `build-service`, `docker-deploy-ecr`, `update-backend-version`, Artifactory OIDC |
| Legacy actions | `barracuda-internal/neutron-actions@v1.x` | Only account-service — migrate off |
| Coverage gate pattern | api-service / ai-service `CI.yaml` | `CODE_COVERAGE_TARGET` repo variable + `LouisBrunner/checks-action` |
| Vulnerability scan | `barracuda-internal/bn-securedev-cicd/actions/bn-vuln-hunter` | Pin `@v2`, not `@main` |
| TFLint config | [templates/tflint.hcl](../templates/tflint.hcl) (from `nexus-terraform/.tflint.hcl`) | Typed variables, documented outputs, naming convention, AWS plugin |
| Terraform plan/apply flow | `nexus-terraform/.github/workflows/` | Plan-with-PR-comment, manual apply gates, OIDC auth, concurrency control |
| GitOps structure | `nexus-argocd` (base/overlays), `nexus-charts` | Deployment order documented in charts README; promotion via PRs to per-environment `versions/` files |
| Helm chart gates | `nexus-charts/.github/workflows/` | `helm lint` + rendered chart-diff PR comments; shared `nexus-app-generic` base chart; Renovate for chart versions |
| Kustomize/K8s lint | `nexus-argocd/argocd-lint/` | Custom Checkov checks + `kubectl kustomize` build validation |
| Kafka schema CI | `nexus-schemas` | Topic JSON Schemas validated and registered to Confluent Schema Registry on merge |
| PR template with AI testing notes | `nexus-ui-host/.github/PULL_REQUEST_TEMPLATE.md` | Auto-generated AI testing notes on merge, opt-out checkbox |
| Role-based e2e auth | `nexus-ui-host/e2e/playwright.config.ts` | Per-role auth setup projects with dependency chaining |
| License compliance precedent | `bds/THIRD_PARTY_LICENSES.md`, `bds/RESOLUTIONS.md` | Owner, key storage, renewal cycle; documented dependency resolutions with exit criteria |
| FOSSA platform integration | app.fossa.com (org GitHub integration) | License + security status per repo (badges in e.g. product-state-service README); scans platform-side, not yet a PR gate |

## Existing AI Automation (Claude API, provisioned fleet-wide)

`ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` repo secrets power production CI
automation today (23 workflow references):

- `update-docs.yml` in every backend repo — headless Claude doc sync
- `build-and-deploy` — AI-generated testing notes on merge
- `nexus-architecture` — bi-weekly root architecture verification and Jira
  ticket transitions

Copilot reviews PRs; Claude maintains docs and automates tickets. A Tier 3
structured-review adapter would share these already-provisioned credentials.

## Shared CI Credentials (referenced across fleet workflows)

| Secret | Purpose |
| --- | --- |
| `NEXUS_GH_APP_CLIENT_ID` / `NEXUS_GH_APP_PRIVATE_KEY`, `NEXUS_APP_ID` / `NEXUS_APP_PRIVATE_KEY` | Nexus GitHub App — mints scoped tokens for CI (the workhorse; 130+ references) |
| `JIRA_API_TOKEN` / `JIRA_USER_EMAIL` | Jira ticket automation |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` | Claude API — doc sync, testing notes, ticket automation |
| `BNSEC_SECUREDEV_IQ_API_KEY` / `PLATFORM_CI_IQ_KEY` | bn-vuln-hunter scanning |
| `FOSSA_API_KEY` | FOSSA CI scans |
| `CUDA_NETWORKS_GITHUB_AUTH_TOKEN` | Cross-org GitHub access |
| `GIST_AUTH_TOKEN` | Coverage badge gists |
| `DATABRICKS_TOKEN` / `DATABRICKS_HOST` | api-service value-report resync |
| `AZURE_CREDENTIALS` | Azure operations (Entra ID) |
| `ARTIFACTORY_USER` / `ARTIFACTORY_PASSWORD` | Artifactory (static — see gaps; OIDC preferred) |
| `AWS_RDS_USERNAME` / `AWS_RDS_PASSWORD` | Deploy-time database migrations (nexus-argocd) |

## Documented Gaps (candidates for future standards work)

- Environment promotion flow (dev → qa → prod) exists in practice but is not
  written down.
- Database migration rollback runbooks.
- Commit message format beyond the Jira ticket reference.
- Org-wide action version matrix (checkout/setup-dotnet currently
  inconsistent across repos).
- .NET version drift: account-service is still on .NET 8 while the rest of
  the backend fleet is on .NET 10; account-service also lacks a `CLAUDE.md`.
- AGENTS.md adoption: only ai-service has one; the other backend repos rely
  on `CLAUDE.md` alone.
- No repository has a `.guardrails/` install yet — Guardrails adoption has
  not started on the Nexus fleet.
- `nexus-service-template` is on .NET 8 while the fleet standard is .NET 10
  — new services start behind until the template is upgraded.
- Convention adherence baseline (NEX-4157, 2026-05): audited repos scored
  46–82/100 against the C# conventions — see
  `nexus-architecture/repo-auditing/` for the scored findings.
- Credential hygiene (found by sweeping `secrets.*` across fleet
  workflows): static `AWS_RDS_USERNAME`/`AWS_RDS_PASSWORD` in
  nexus-argocd database-deploy workflows (runtime uses IAM; deploy-time
  does not); static `ARTIFACTORY_USER`/`PASSWORD` in some repos while
  others use Artifactory OIDC; a stray `GH_PAT` where the GitHub App
  should be used; naming drift (`JIRA_TOKEN` vs `JIRA_API_TOKEN`,
  lowercase `secrets_app_id`); unexplained `SES_K` in nexus-terraform
  workflows — audit and standardize.
