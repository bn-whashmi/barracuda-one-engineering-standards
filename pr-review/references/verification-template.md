# Review Verification Template

Each resolved finding should capture:

- **Validation method:** test, build, lint, targeted reproduction, or static
  proof.
- **Command:** the exact command, when applicable.
- **Result:** `passed`, `failed`, or `partial`.
- **Evidence:** the relevant output, trace, or reasoning.
- **Residual risk:** remaining uncertainty or accepted limitation.

If verification is partial, keep the finding `blocked` or `needs-context` until
the missing evidence is supplied or an explicit risk owner accepts it.
