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

## CI/CD Assets

| Asset | Location | Notes |
| --- | --- | --- |
| Shared CI actions | `barracuda-internal/nexus-actions@v2` | PR title/checklist validators (`jira_projects: NEX`), Jira transitions, `build-service`, `docker-deploy-ecr`, `update-backend-version`, Artifactory OIDC |
| Legacy actions | `barracuda-internal/neutron-actions@v1.x` | Only account-service — migrate off |
| Coverage gate pattern | api-service / ai-service `CI.yaml` | `CODE_COVERAGE_TARGET` repo variable + `LouisBrunner/checks-action` |
| Vulnerability scan | `barracuda-internal/bn-securedev-cicd/actions/bn-vuln-hunter` | Pin `@v2`, not `@main` |
| TFLint config | [templates/tflint.hcl](../templates/tflint.hcl) (from `nexus-terraform/.tflint.hcl`) | Typed variables, documented outputs, naming convention, AWS plugin |
| Terraform plan/apply flow | `nexus-terraform/.github/workflows/` | Plan-with-PR-comment, manual apply gates, OIDC auth, concurrency control |
| GitOps structure | `nexus-argocd` (base/overlays), `nexus-charts` | Deployment order documented in charts README; promotion flow dev→qa→prod is implicit — a documentation gap |
| PR template with AI testing notes | `nexus-ui-host/.github/PULL_REQUEST_TEMPLATE.md` | Auto-generated AI testing notes on merge, opt-out checkbox |
| Role-based e2e auth | `nexus-ui-host/e2e/playwright.config.ts` | Per-role auth setup projects with dependency chaining |
| License compliance precedent | `bds/THIRD_PARTY_LICENSES.md`, `bds/RESOLUTIONS.md` | Owner, key storage, renewal cycle; documented dependency resolutions with exit criteria |

## Documented Gaps (candidates for future standards work)

- Environment promotion flow (dev → qa → prod) exists in practice but is not
  written down.
- Database migration rollback runbooks.
- Commit message format beyond the Jira ticket reference.
- Org-wide action version matrix (checkout/setup-dotnet currently
  inconsistent across repos).
