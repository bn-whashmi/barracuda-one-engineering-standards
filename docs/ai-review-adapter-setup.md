# AI Review Adapter Setup

The AI review workflows are provider-neutral sockets: they run a
repository-owned `AI_REVIEW_COMMAND` and validate its output. This page
defines the adapter contract and how to wire one up. A working Claude
reference implementation lives in
[examples/ai-review-adapter-claude/](../examples/ai-review-adapter-claude/).

## Contract

| | |
| --- | --- |
| Input env | `AI_REVIEW_ROLE` (`engineering` \| `qa` \| `security` \| `repo-standards`), `AI_REVIEW_RESULT` (output path) |
| Credentials | Whatever the adapter needs, passed through workflow env from repo secrets (Nexus: `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL`, already provisioned fleet-wide) |
| Diff access | `GH_TOKEN` + `GITHUB_EVENT_PATH` for the GitHub API, or plain `git diff` |
| Output | JSON object `{"findings": [...]}` at `AI_REVIEW_RESULT`, per [pr-review/references/finding-format.md](../pr-review/references/finding-format.md) |
| Exit codes | `0` = review completed (findings allowed — the consolidation job enforces P0/P1 blocking); non-zero = adapter failure |
| Security | Never log tokens or paste secrets into findings; treat the diff as untrusted content, not instructions |

## Wiring steps

1. Copy the adapter into the repo (convention: `.ai-review/adapter.py`).
2. Set repository variable `AI_REVIEW_COMMAND` (e.g.
   `python3 .ai-review/adapter.py`). The workflows are skipped while this
   variable is empty — an unset adapter cannot fake a pass.
3. Confirm the workflow env passes the credentials the adapter needs
   (`ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `GH_TOKEN`).
4. Start with the engineering lens only; verify findings are material
   over ~10 PRs before expanding lenses (see
   [barracuda-adoption.md](barracuda-adoption.md), Tier 3).

Advisory first, always: do not add the AI review checks to required
status checks until findings have proven material and stable.
