# Claude AI Review Adapter

Working reference adapter that plugs Claude into the provider-neutral AI
PR review workflows (`workflows/ai-pr-review.yml` and the per-lens
`.github/workflows/ai-*.yml`). Stdlib-only Python — no pip installs.

## How it works

The review workflows run `AI_REVIEW_COMMAND` with `AI_REVIEW_ROLE` set to
one of `engineering | qa | security | repo-standards` and expect a JSON
object `{"findings": [...]}` at `AI_REVIEW_RESULT`. This adapter:

1. Fetches the PR diff (GitHub API via `GH_TOKEN`, falling back to
   `git diff origin/main...HEAD`).
2. Loads repo context if present: `pr-review/barracuda-context.md`,
   `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`.
3. Calls the Anthropic Messages API with a role-specific reviewer prompt.
4. Writes findings per `pr-review/references/finding-format.md`.

The adapter always exits 0 when it produced a valid result — blocking on
unresolved P0/P1 findings is enforced by the consolidation job, not here.

## Setup (this repo or any Nexus repo)

1. Secrets (already provisioned fleet-wide on Nexus repos):
   `ANTHROPIC_API_KEY`, and `ANTHROPIC_BASE_URL` if you use a proxy.
2. Copy this adapter into the repo (convention: `.ai-review/adapter.py`).
3. Set the repository variable:
   `AI_REVIEW_COMMAND = python3 .ai-review/adapter.py`
   (in this standards repo: `python3 examples/ai-review-adapter-claude/adapter.py`)
4. Ensure the AI review workflows pass the credentials through — the
   workflow env must include `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`,
   and `GH_TOKEN` (the copies in this repo already do).

## Tuning

| Env var | Default | Purpose |
| --- | --- | --- |
| `AI_REVIEW_MODEL` | `claude-sonnet-4-5` | Model override |
| `AI_REVIEW_MAX_DIFF_CHARS` | `160000` | Diff truncation limit |
| `AI_REVIEW_BASE` | `origin/main` | Fallback git diff base |

## Local test

```sh
export ANTHROPIC_API_KEY=... AI_REVIEW_ROLE=engineering \
       AI_REVIEW_RESULT=/tmp/findings.json
python3 adapter.py   # from a branch with changes vs origin/main
cat /tmp/findings.json
```
