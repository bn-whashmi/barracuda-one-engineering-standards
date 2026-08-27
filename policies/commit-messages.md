# Commit Message Policy

Use concise, auditable commit messages that explain the engineering or product
outcome without creating unnecessary process.

## Format

```text
<type>: <imperative summary>
```

Common types:

- `fix` — bug, regression, security, or data-integrity correction.
- `feat` — new or expanded capability.
- `chore` — maintenance, dependency, repository, or operational cleanup.
- `docs` — documentation-only change.
- `test` — test-only change.
- `refactor` — internal restructuring without intended behavior change.
- `ci` — CI, automation, or workflow change.
- `revert` — reversal of a previous commit.

## Rules

- Use imperative voice: `fix`, `add`, `remove`, `document`.
- Keep the subject under 72 characters when practical.
- State the user-visible or operational outcome, not only the file changed.
- Prefer one coherent reason per commit.
- Never include secrets, credentials, tokens, customer data, or private
  incident details.
- Reference the issue or PR in the body when the repository uses issue
  tracking.
