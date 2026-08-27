# Error Handling and Observability Policy

Use this policy for production-facing code. The goal is diagnosable failure
without leaking sensitive data or turning normal user interruptions into noisy
incidents.

## Core rules

- Do not use force-unwrapping, panic-style shortcuts, or equivalent runtime
  crash paths for recoverable production failures.
- Avoid silent `catch {}`, broad `except`, or ignored promise rejections on
  stateful paths unless the failure is intentionally ignorable and documented.
- Return or throw typed/domain errors from service, transport, and integration
  layers when practical.
- Catch failures at feature, route, job, application-state, or UI boundaries.
- Distinguish cancellation, validation, permission, not-found, provider
  failure, and unexpected internal failure.

## User-facing errors

- Use calm, non-technical copy.
- Do not expose stack traces, SQL, provider payloads, environment names,
  credential names, tokens, or internal exception text.
- Tell the user what happened and what they can do next when action is
  possible.

## Operator-facing diagnostics

Unexpected recoverable failures and 5xx paths should log structured context:

- `request_id` or correlation ID when available.
- `feature`, `route`, `job`, or `action`.
- Safe entity IDs when useful.
- Provider or integration name when applicable.
- An outcome such as `recoverable`, `service_failure`,
  `validation_failed`, or `internal_error`.

Never log secrets, access tokens, authentication artifacts, invite codes, raw
customer payloads, private files, or unnecessary PII.

## API and client expectations

- Validation, authentication, permission, and not-found paths should return
  typed 4xx responses.
- Unexpected server failures should return safe public response bodies and log
  details internally.
- API responses should include or propagate a request ID where practical.
- Cancellation should usually return quietly.
- Local persistence corruption should prefer log plus recovery over silent
  failure.
- State-loss paths should record enough context to reconstruct the failure.
