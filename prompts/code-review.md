# Code Review Prompt

Review the current change as a senior engineer.

Focus on:

- Correctness bugs and regressions.
- Security, privacy, auth, and permission boundaries.
- Data model, migration, and compatibility risks.
- Missing tests for changed behavior.
- Operational risks: deploy, rollback, logging, and observability.
- Overbroad changes that should be split.

Output format:

```text
Findings
- severity: file:line - issue and impact

Questions
- unresolved assumptions

Verification Gaps
- checks not run or coverage missing
```

Do not summarize first. Findings come first, ordered by severity.
