# Sample Guardrail Scorecard

This is a representative report from the embedded Python example. Values vary by
revision and by which producers the repository has connected.

```text
╔══════════════════════════════════════════════════════════════════════╗
║                            GUARDRAIL SCAN                            ║
╚══════════════════════════════════════════════════════════════════════╝
  RESULT       ORANGE — ALLOW
  ENFORCED     0/0 passed (0%)
  ADVISORY     7/19 passed — non-blocking
  READINESS    ORANGE (enforced RED: 0)

Detailed controls
-----------------
STATUS  ENFORCEMENT  ACTIVATION     EVIDENCE   CONTROL
GREEN   advisory     github-native   PASSED     unit-tests — Unit Tests
GREEN   advisory     github-native   PASSED     dependency-review — Dependency Review
GREEN   advisory     github-native   PASSED     dependabot — Dependabot
RED     advisory     repository      FAILED     repository-ground-truth — Ground Truth
ORANGE  advisory     github-native   NO RESULT  codeql-sast — CodeQL / SAST
ORANGE  advisory     external        NO RESULT  sonarqube — SonarQube
ORANGE  advisory     external        NO RESULT  snyk-code — Snyk Code

Findings
--------
- [advisory] repository-ground-truth: FAILED — declared documents are missing
- [advisory] codeql-sast: NO RESULT — producer has not reported this revision
- [advisory] sonarqube: NO RESULT — producer has not reported this revision
```

How to read it:

- `GREEN` means the selected producer passed for the exact revision.
- `ORANGE` means the control is selected but has no result yet.
- `RED` means the producer failed; it only blocks when enforcement is `enforced`.
- `enforced` and `advisory` describe policy behavior. `not_activated` means the
  repository has not selected the control.

See the [Python example](../../examples/python-demo/)
for a runnable example and the [compliance runbook](../compliance.md) for the
commands that generate reports like this one.
