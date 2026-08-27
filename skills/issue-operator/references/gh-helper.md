# GH Helper

Use `scripts/gh_issue_helper.py` when GitHub issue sync should follow the same deterministic state model as `project-audit-findings.md` and `full-test-suite-report.md`.

## Sync all actionable findings

```bash
python3 scripts/gh_issue_helper.py sync \
  --repo-root . \
  --findings-path project-audit-findings.md \
  --report-path full-test-suite-report.md
```

Behavior:

- reads `confirmed-open`, `in-progress`, and `resolved` findings
- searches existing issues by finding ID before creating anything
- creates or edits GitHub issues from the shared finding record
- writes `#issue-number` back into `project-audit-findings.md`
- closes issues only when the finding is `resolved` and verification is recorded
- records created, updated, and closed issues in `full-test-suite-report.md` when `--report-path` is provided

Useful options:

- `--repo owner/name`: force a specific GitHub repo
- `--gh-binary /path/to/gh`: use a non-default `gh` binary
- `--dry-run`: compute actions without mutating GitHub or local files
