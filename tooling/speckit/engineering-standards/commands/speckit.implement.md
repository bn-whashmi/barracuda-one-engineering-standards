## Engineering Standards Wrapper

When implementing:

- Work from `tasks.md` in order unless a dependency or user instruction changes
  the sequence.
- Keep the spec and plan current when implementation reveals drift.
- Preserve unrelated user changes.
- Run the narrowest meaningful checks first, then broader release gates when
  risk justifies them.
- Record skipped checks, release evidence, rollback notes, and known gaps for
  production-facing work.

{CORE_TEMPLATE}
