## Engineering Standards Wrapper

Before and after the upstream planning workflow:

- Identify the repository's validation model and use checks available in that
  model.
- Include security, privacy, error-handling, observability, parity, and contract
  gates when the feature touches those areas.
- For production-facing work, identify deployment target, rollback path, and
  release evidence location before implementation.
- Keep technical decisions in `plan.md`; update `spec.md` only when product
  intent changes.

If a gate cannot be satisfied, record the reason and the follow-up owner in the
plan instead of silently proceeding.

{CORE_TEMPLATE}
