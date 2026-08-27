# Manifest Loop

Use `full-test-suite-manifest.json` as the deterministic orchestration record for the bundle run.

## What the manifest tracks

- selected skills for the chosen profile
- active cycle and cycle history
- whether GitHub issue sync is pending
- whether a clean post-fix full scan is still required
- fix history and rerun scheduling
- next-step planning state

## Convergence rule

Do not treat the run as complete just because the current fix queue is empty.

The runner converges only after:

1. the current actionable findings have been fixed or otherwise cleared
2. impacted rerun skills have completed
3. GitHub issue sync has been reconciled
4. a fresh full scan cycle has completed after the last applied fix
5. that clean full scan produced no new `confirmed-open` or `in-progress` findings

## Core loop

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

Then repeat:

1. `python3 scripts/full_test_suite_runner.py next-action --manifest-path full-test-suite-manifest.json`
2. Follow the returned action:
   - `run-skill`: run that skill, then `record-skill`
   - `fix-finding`: fix that finding, update `project-audit-findings.md`, then `record-fix`
   - `sync-issues`: run `sync-issues`
   - `finalize`: run `finalize`
3. Continue until `next-action` returns `finalize`, then finalize the run

## Important commands

- Record a completed skill pass:
  - `python3 scripts/full_test_suite_runner.py record-skill --report-path full-test-suite-report.md --manifest-path full-test-suite-manifest.json --skill bug-hunter --status completed`
- Record a completed fix and enqueue reruns:
  - `python3 scripts/full_test_suite_runner.py record-fix --manifest-path full-test-suite-manifest.json --finding-id BUG-001 --surfaces "App/Services/ExampleBackendClient.swift" --types "bug"`
- Run deterministic GitHub issue sync:
  - `python3 scripts/full_test_suite_runner.py sync-issues --manifest-path full-test-suite-manifest.json`
- Inspect the manifest:
  - `python3 scripts/full_test_suite_runner.py show-manifest --manifest-path full-test-suite-manifest.json`
