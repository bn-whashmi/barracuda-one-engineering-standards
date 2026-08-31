# Barracuda Adoption Guide

How a Nexus repository adopts these standards, tier by tier. Uses the
Guardrails installer — see [quickstart.md](quickstart.md) for generic
installation details.

## Week 1 — Tier 1: Mechanical

1. Install the Core runtime:

   ```sh
   python3 /path/to/barracuda-one-engineering-standards/tooling/install.py --target /path/to/repo
   ```

2. Configure real repo commands as GitHub repository variables (an unset
   command skips the producer — it cannot fake a pass):

   ```sh
   # .NET service example
   GUARDRAILS_BUILD_COMMAND='dotnet build --no-restore'
   GUARDRAILS_UNIT_TEST_COMMAND='dotnet test --no-build'
   # Frontend example
   GUARDRAILS_BUILD_COMMAND='yarn build'
   GUARDRAILS_UNIT_TEST_COMMAND='yarn test:unit'
   ```

3. Add the Barracuda Semgrep rules from
   [security/semgrep/barracuda.yml](../security/semgrep/barracuda.yml) to the
   repo's `.guardrails/semgrep-rules.yml`.

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
2. SonarQube (`static-quality`) — quality gate on new code.
3. Snyk — decide the authoritative product per finding class before enabling
   both Open Source and Code. Today most Nexus repos run
   `bn-vuln-hunter`; keep it supplemental once Snyk is authoritative, or
   keep bn-vuln-hunter authoritative and skip Snyk — pick one, document it.
4. FOSSA (`license-compliance`) — when an owner is assigned.

**Exit criteria per provider:** reliable results on representative PRs, tuned
thresholds, named owner. Only then require its exact status context.

## When Ready — Tier 3: AI

1. Wire the AI review workflows with your provider adapter.
2. Start with engineering review only; verify findings are material over
   ~10 PRs, using [pr-review/barracuda-context.md](../pr-review/barracuda-context.md)
   so reviewers know intentional platform patterns (fail-open Redis, error
   masking, gateway-delegated JWT validation).
3. Expand to QA, security, and repo-standards lenses one at a time.

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
- No repo currently runs CodeQL, SonarQube, Snyk, or secret-detection —
  these are Tier 2 targets, not existing coverage.

## Common Mistakes

- Enforcing before verifying — a workflow file proves nothing; the check
  must report correctly on real PRs first.
- Duplicating org-level branch protection in repo rulesets.
- Copying templates without editing them.
- Enabling two blocking scanners for the same finding class without a
  documented defense-in-depth decision.
