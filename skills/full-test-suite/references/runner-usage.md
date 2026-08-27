# Runner Usage

Use `scripts/full_test_suite_runner.py` to manage run state deterministically while the skill suite does the actual analysis and fixing.
Prefer the manifest-driven loop in `manifest-loop.md` when you want the bundle to run to convergence.
Prefer `executor.md` when you want the loop to actually execute through `codex exec` instead of stepping it manually.

## Initialize a run

```bash
python3 scripts/full_test_suite_runner.py init \
  --repo-root . \
  --findings-path project-audit-findings.md \
  --report-path full-test-suite-report.md \
  --manifest-path full-test-suite-manifest.json \
  --scope "repo-wide" \
  --mode default \
  --profile core
```

The init response includes the first `next_action`.

## Ask for the next step

```bash
python3 scripts/full_test_suite_runner.py next-action \
  --manifest-path full-test-suite-manifest.json
```

## Record skill completion

```bash
python3 scripts/full_test_suite_runner.py record-skill \
  --report-path full-test-suite-report.md \
  --manifest-path full-test-suite-manifest.json \
  --skill bug-hunter \
  --status completed \
  --note "Focused on claim redemption flow"
```

## Refresh the fix queue

```bash
python3 scripts/full_test_suite_runner.py plan-fixes \
  --findings-path project-audit-findings.md \
  --report-path full-test-suite-report.md
```

## Suggest impacted reruns after a fix

```bash
python3 scripts/full_test_suite_runner.py suggest-rerun \
  --profile deep-audit \
  --surfaces "services/pbrotator-api/src/routes/share.ts,services/pbrotator-api/src/env.ts" \
  --types "api-contract,config"
```

## Record a completed fix

```bash
python3 scripts/full_test_suite_runner.py record-fix \
  --manifest-path full-test-suite-manifest.json \
  --finding-id BUG-001 \
  --surfaces "App/Services/ExampleBackendClient.swift" \
  --types "bug"
```

## Run GitHub issue sync

```bash
python3 scripts/full_test_suite_runner.py sync-issues \
  --manifest-path full-test-suite-manifest.json
```

## Inspect the manifest

```bash
python3 scripts/full_test_suite_runner.py show-manifest \
  --manifest-path full-test-suite-manifest.json
```

## Finalize the run

```bash
python3 scripts/full_test_suite_runner.py finalize \
  --repo-root . \
  --findings-path project-audit-findings.md \
  --report-path full-test-suite-report.md \
  --manifest-path full-test-suite-manifest.json
```
