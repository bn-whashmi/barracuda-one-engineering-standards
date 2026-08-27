# Codex Instructions

Use this repository's `AGENTS.md` as the primary source of engineering context.

## Defaults

- Inspect the repo before making assumptions.
- Prefer small, reviewable changes.
- Preserve unrelated local changes.
- Add tests for changed behavior when practical.
- Do not introduce new dependencies without a clear reason.
- Avoid broad rewrites when a targeted fix is sufficient.
- Do not include secrets, tokens, customer data, or private operational details.

## Commit And Change Summary Expectations

- Use the repository commit-message standard.
- Include verification performed in final summaries, issue notes, or PR notes
  when a repository chooses to use PRs.
- Call out risk and rollback for production-facing changes.
- Keep commits scoped to one coherent outcome.
- Pull requests are required for default-branch changes. A single-developer
  repository may use zero required approvals; teams can raise the approval
  count as their review needs grow.

## Autonomy

- Continue through implementation and verification when the request is explicit.
- Stop and ask before destructive operations, branch deletion, force pushes, or
  changes that could expose sensitive data.
- If local state is dirty, preserve unrelated edits and stage only the intended
  files.
