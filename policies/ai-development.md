# AI Development Policy

## Status

This is an organization-wide baseline. Repository-specific AI instructions
remain in the application repository's `AGENTS.md` and related ground-truth
documents.

## Requirements

- AI-assisted development is the default engineering tool for normal work.
- Engineers remain accountable for everything they commit, approve, and merge.
- Use AI for code understanding, planning, implementation, testing,
  debugging, documentation, and review when it improves the work.
- Human intervention remains appropriate for difficult architectural,
  ambiguous, novel, or high-risk problems.
- AI-generated code is subject to the same or higher quality, testing,
  security, and review requirements as human-written code.
- AI speed must not bypass branch protection, testing, security scanning,
  review, or release controls.
- Do not include secrets, credentials, private customer data, or unnecessary
  sensitive operational details in prompts, generated artifacts, or review
  comments.
- Verify generated code against the application repository's ground truth
  before merging. Do not invent architecture, APIs, commands, or security
  guarantees when the repository does not document them.

## Accountability

AI may propose or perform work, but the engineer who submits the change owns
its correctness, security, maintainability, and operational consequences.
