# Executor

Use `scripts/full_test_suite_executor.py` when you want the bundle to actually execute the manifest-driven loop through `codex exec`.
It prints live progress plus a compact end-of-step summary to stderr by default and leaves the final machine-readable result on stdout.

## One-command run

```bash
python3 scripts/full_test_suite_executor.py run \
  --repo-root . \
  --profile core \
  --max-steps 50
```

Use `--reinit` if you want to discard the prior manifest state and start a fresh run in the same repository.
Use `--quiet` if you want to suppress live progress output.

## Single step

```bash
python3 scripts/full_test_suite_executor.py step \
  --manifest-path full-test-suite-manifest.json
```

This reads `next-action` from the manifest and then:

- runs `codex exec` for `run-skill`
- runs `codex exec` for `fix-finding`
- runs deterministic issue reconciliation for `sync-issues`
- runs finalization for `finalize`

## Full loop

```bash
python3 scripts/full_test_suite_executor.py loop \
  --manifest-path full-test-suite-manifest.json \
  --max-steps 50
```

## Notes

- default execution uses `codex exec --full-auto`
- use `--codex-binary /path/to/codex` to override the CLI path
- use `--model <model>` or `--config-profile <profile>` if you want a specific Codex configuration
- use `--danger-full-access` only when the environment is externally sandboxed and you explicitly want the executor to bypass Codex CLI safety rails
- use `--quiet` to suppress progress lines and keep the command mostly silent until completion
