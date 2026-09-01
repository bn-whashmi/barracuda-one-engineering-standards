# Barracuda Adoption Guide

How a Nexus repository adopts these standards, tier by tier. Uses the
Guardrails installer — see [quickstart.md](quickstart.md) for generic
installation details.

## Week 1 — Tier 1: Mechanical

Nexus repos already run most Tier 1 checks: every backend has a `CI`
workflow (restore, build, `dotnet format` verification, tests, and coverage
via `nexus-actions@v2` `build-service` and the `CODE_COVERAGE_TARGET`
variable), and nexus-ui-host runs `Check ESLint`, `Check Prettier`,
`Check Typescript`, and `Run Unit Tests`. **Do not install duplicate
build/test workflows on top of these** — Week 1 is about wiring what
already runs into the evidence layer, plus adding the checks no repo has.

1. Install the Core runtime:

   ```sh
   python3 /path/to/barracuda-one-engineering-standards/tooling/install.py --target /path/to/repo
   ```

   Then delete the copied `build.yml`, `unit-tests.yml`, and
   `changed-code-coverage.yml` templates — the repo's existing `CI`
   workflow already covers build, tests, formatting, and coverage.

2. Register the existing CI as the producer for those controls in the
   repo's `.guardrails/providers.yaml`: point `build` and `unit-tests` at
   the existing check (backend: `check_name: "CI / Build"`,
   `workflow_path: .github/workflows/CI.yaml`; frontend: the
   `Run Unit Tests` and lint check names). The scorecard then collects
   evidence from the CI the repo already runs. (Only a repo with no build
   CI at all should keep the stock templates and configure
   `GUARDRAILS_BUILD_COMMAND` / `GUARDRAILS_UNIT_TEST_COMMAND` repository
   variables instead — an unset command skips the producer; it cannot fake
   a pass.)

3. What Week 1 actually adds:
   - Secret detection: already covered — GitHub Secret Protection is
     enabled org-wide with validity checks, extended metadata, generic
     patterns, and push protection. Do not add `gitleaks.yml`; just verify
     the settings under Settings → Advanced Security on the repo.
   - `semgrep-ce.yml`, with the Barracuda rules from
     [security/semgrep/barracuda.yml](../security/semgrep/barracuda.yml)
     copied into the repo's `.guardrails/semgrep-rules.yml`.
   - `repository-validation.yml` — repo, docs, ground-truth, and
     change-scope validators.
   - `guardrails-scorecard.yml` — evidence collection and the PR scorecard
     comment.

4. Copy and **edit** the templates: `templates/AGENTS.md`,
   `templates/CLAUDE.md`. An unedited template misleads AI reviewers.

5. Branch protection: baseline rules (PR required, no force push, no
   deletion) are owned by the **organization-level ruleset** — verify
   coverage under Settings → Rules → Rulesets and do not duplicate them.
   Import [rulesets/barracuda-required-status-checks.json](../rulesets/barracuda-required-status-checks.json)
   as the empty per-repo container for required checks.

**Exit criteria:** core scorecard green on three representative PRs. Then
promote the mechanical checks by adding their exact status contexts to the
repo ruleset.

## Weeks 2–4 — Tier 2: 3rd Party

Adopt one provider at a time (see
[barracuda-three-tier-model.md](barracuda-three-tier-model.md) for the map,
[control-setup.md](control-setup.md) for mechanics):

1. GitHub profile first (no new vendor):
   `python3 tooling/install.py --target /path/to/repo --profile github`
   Much of this is existing coverage to verify, not adopt: Secret
   Protection (full feature set) and Dependabot alerts + dependency graph
   are already enabled — the profile's verification checks confirm them
   and bind the evidence. The real gap is **CodeQL** (`deep-sast`): enable
   default setup per repo. This also activates Copilot Autofix, which is
   already licensed and toggled on but idle until CodeQL produces alerts.
2. SonarQube (`static-quality`) — quality gate on new code.
3. Snyk — three scanners now overlap on dependency vulnerabilities:
   Dependabot (already enabled), `bn-vuln-hunter` (runs in most repos),
   and Snyk (not adopted). Pick the authoritative product per finding
   class and document it; skipping Snyk entirely because Dependabot +
   bn-vuln-hunter already cover the class is a legitimate outcome.
4. FOSSA (`license-compliance`) — when an owner is assigned.

**Exit criteria per provider:** reliable results on representative PRs, tuned
thresholds, named owner. Only then require its exact status context.

## When Ready — Tier 3: AI

GitHub Copilot PR review already runs on Nexus repositories — it is the
incumbent Tier 3 producer. Today it reviews without platform context and
without structured findings, so adoption means grounding and structuring
what already runs, not adding AI review from scratch:

1. Ground Copilot with platform context: feed
   [pr-review/barracuda-context.md](../pr-review/barracuda-context.md) and
   the lens guides via the repo's `.github/copilot-instructions.md`, so it
   stops flagging intentional platform patterns (fail-open Redis, error
   masking, gateway-delegated JWT validation) and knows the account-
   hierarchy authorization model.
2. Decide the authoritative Tier 3 provider and document it — Copilot
   grounded with the lens prompts, or a separate adapter wired through the
   AI review workflows (same pick-one rule as bn-vuln-hunter vs Snyk).
   Structured JSON findings, P0–P3 severities, and scorecard evidence
   require the adapter route; grounded Copilot alone stays advisory
   commentary.
3. Start with the engineering lens only; verify findings are material over
   ~10 PRs. Expand to QA, security, and repo-standards lenses one at a
   time.

## Known CI Standardization Gaps (as of 2026-08)

Found by auditing the five main backend repos — fix these during adoption:

- `nexus-backend-account-service` still uses `neutron-actions@v1` and has no
  coverage enforcement — migrate to `nexus-actions@v2` + `CODE_COVERAGE_TARGET`.
- `nexus-backend-graphql-mesh-gateway` publishes coverage but does not gate
  on it in PR CI.
- `bn-vuln-hunter` is pinned to `@main` in three repos and `@v2` in one —
  standardize on the version pin.
- `actions/checkout` split across v4/v7 and `actions/setup-dotnet` across
  v4/v6 — align to the newest verified versions.
- CodeQL needs setup on every repo — Copilot Autofix is licensed and
  toggled on but idle until CodeQL produces alerts. SonarQube and FOSSA
  are not adopted anywhere. (Secret Protection and Dependabot are already
  enabled — existing coverage, not gaps.)
- Copilot PR review runs without barracuda-context grounding or structured
  findings — reviews are generic and produce no scorecard evidence.

## Common Mistakes

- Enforcing before verifying — a workflow file proves nothing; the check
  must report correctly on real PRs first.
- Installing the stock build/test workflow templates on a repo whose CI
  already builds and tests — register the existing checks as producers in
  `.guardrails/providers.yaml` instead.
- Duplicating org-level branch protection in repo rulesets.
- Copying templates without editing them.
- Enabling two blocking scanners for the same finding class without a
  documented defense-in-depth decision.
