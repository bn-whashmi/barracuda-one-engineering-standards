# Barracuda Three-Tier Control Model

An organizational lens over the [control catalog](../policies/control-catalog.yaml)
and [profiles](../policies/profiles.yaml). It does not change the catalog or
runtime — it groups capabilities by what they depend on, which determines
adoption order and ownership at Barracuda.

| Tier | Definition | Depends on |
| --- | --- | --- |
| **1 — Mechanical** | Deterministic checks runnable anywhere, including local OSS tools with no account | Nothing external |
| **2 — 3rd Party** | Checks requiring an external provider account, platform feature, or environment | Credentials + provider activation |
| **3 — AI** | AI-powered review with structured evidence | AI provider access |

Tier 1 roughly equals the `core` profile; Tier 2 covers the `github` profile
plus external vendors; Tier 3 is the four AI reviews.

## Catalog Mapping

### Tier 1 — Mechanical

| Control | Barracuda producer |
| --- | --- |
| `repository-validation` | Guardrails runtime |
| `documentation-validation` | Guardrails runtime |
| `repository-ground-truth` | Guardrails runtime |
| `change-scope` | Guardrails runtime |
| `build` | `dotnet build` / `yarn build` / `terraform validate` |
| `unit-tests` | xUnit / Jest (see coverage targets in [barracuda-platform.md](../policies/barracuda-platform.md)) |
| `changed-code-coverage` | Coverlet / Jest coverage |
| `custom-static-analysis` | Existing linters — ESLint `no-restricted-imports` (frontend), Roslyn analyzers / banned APIs (.NET); rule catalog in [barracuda.yml](../security/semgrep/barracuda.yml) (Semgrep runner not adopted) |
| `secret-detection` | Gitleaks CLI |

### Tier 2 — 3rd Party

| Control | Barracuda producer / provider |
| --- | --- |
| `deep-sast` | CodeQL (GitHub profile; also activates licensed Copilot Autofix) |
| `dependency-change-review` | GitHub Dependency Review |
| `platform-secret-protection` | GitHub Secret Protection |
| `dependency-remediation` | Dependabot |
| `artifact-provenance` | GitHub Artifact Attestations |
| `static-quality` | Not adopted — covered by coverage gate + linters + grounded Copilot review (SonarQube only on concrete need) |
| `dependency-vulnerability` | Dependabot + `bn-securedev-cicd/bn-vuln-hunter` + FOSSA security (Snyk not adopted) |
| `license-compliance` | FOSSA (BDS MUI X licensing precedent in `bds/THIRD_PARTY_LICENSES.md`) |
| `runtime-soak`, `container-vulnerability`, `iac-misconfiguration`, `artifact-sbom`, `artifact-vulnerability`, `deployment-policy`, `dynamic-application-security`, `runtime-assurance` | Evidence-only or environment-based; adopt per repo |

### Tier 3 — AI

| Control | Guide |
| --- | --- |
| `ai-engineering-review` | [pr-review/engineering-review.md](../pr-review/engineering-review.md) + [barracuda-context.md](../pr-review/barracuda-context.md) |
| `ai-qa-review` | [pr-review/qa-review.md](../pr-review/qa-review.md) |
| `ai-security-review` | [pr-review/security-review.md](../pr-review/security-review.md) |
| `ai-repository-standards-review` | [pr-review/repo-standards-review.md](../pr-review/repo-standards-review.md) |

## Rules

1. Tiers never block each other — a Tier 2 provider outage must not stop
   Tier 1 checks, and AI reviews never gate deterministic checks.
2. Adopt in tier order: Tier 1 immediately on every repo, Tier 2 one
   provider at a time, Tier 3 one lens at a time (engineering first).
3. Promotion (advisory → enforced) follows the standard promotion rule and
   happens per repo via required status checks — see
   [barracuda-adoption.md](barracuda-adoption.md).
4. Each Tier 2 provider needs a named owner before enforcement.
