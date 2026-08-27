# Guardrails implementation

This directory defines the machine-readable evidence contract:

- `policy.schema.json` describes operations and their required or advisory checks.
- `evidence.schema.json` describes producer results bound to one exact subject revision.
- `baseline.yaml` is a small, replaceable starter policy.

The organization-level connection between checks, producers, evidence, and
status checks lives in [policies/control-catalog.yaml](../policies/control-catalog.yaml).

Policies and evidence use JSON-compatible YAML so the evaluator needs only
Python's standard library. A repository may copy the baseline and change the
check names or enforcement levels. No inheritance or hidden defaults apply.

The policy names evidence; it does not run tools. Tests, SAST, secret scanners,
CI, and reviewers remain independent producers.

Use [compliance.md](compliance.md) for the recommended installation and
scorecard workflow. The scorecard summarizes the evaluator result; it does not
replace the producer tools or turn missing evidence into a pass.
