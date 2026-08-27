## Engineering Standards Principles

### Issue-First Traceability

Meaningful work SHOULD reference a GitHub issue or an equivalent durable work
item. Specs, plans, tasks, commits, and release evidence SHOULD be traceable
back to that work item when practical.

### Release Evidence

Production-facing releases MUST record what shipped, where it shipped, how it
was verified, rollback options, known gaps, and operator notes. The record MUST
avoid secrets, tokens, private customer data, and unsafe operational details.

### Validation Model

Each repository MUST document its selected validation model before enforcing it:
local commands, GitHub Actions, self-hosted runners, another CI system, or a
combination. Plans and tasks MUST use checks that are available to that repo.

### Secure And Observable Behavior

Specs and plans MUST call out sensitive data, authorization boundaries, expected
error behavior, and operator diagnostics for stateful or production-facing
paths.

### Cross-Surface Parity

User-facing behavior that spans multiple clients or deployable surfaces MUST
include parity expectations and independent verification evidence for each
required surface.
