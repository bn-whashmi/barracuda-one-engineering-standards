# Error Handling And Observability Standard

Use `docs/error-handling-standard.md` from this repository as the
canonical source. Copy this file into a product repo when local guidance needs
to travel with the codebase.

## Rules

- No silent stateful failures.
- No secrets, tokens, customer data, raw auth artifacts, invite codes, or
  unnecessary PII in logs.
- Use calm, non-technical user-facing errors.
- Log unexpected failures with stable context: request id, feature/action,
  route/job, safe entity ids, and outcome.
- Distinguish cancellation from failure.
- Add tests or smoke checks for changed error paths when practical.
