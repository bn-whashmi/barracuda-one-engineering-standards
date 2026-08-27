#!/usr/bin/env python3
"""Run the sample tests and write scorecard evidence for this revision."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".artifacts" / "guardrails" / "evidence" / "unit-tests.json"
EVIDENCE_DIR = ROOT / ".artifacts" / "guardrails" / "evidence"


def run_check(check_id: str, producer: str, command: list[str], *, evidence: list[str] | None = None) -> dict:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    details = evidence or ["command: " + " ".join(command)]
    output = (result.stdout + result.stderr).strip()
    if output:
        details.append(output[-1000:])
    return {
        "producer": producer,
        "status": "passed" if result.returncode == 0 else "failed",
        "evidence": details,
    }


def change_scope_check() -> dict:
    command = ["git", "diff", "--numstat", "HEAD^", "HEAD"]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        return {
            "producer": "sample change-scope producer",
            "status": "not_run",
            "reason": "The repository does not have a comparable parent revision.",
        }
    additions = deletions = files = 0
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        try:
            additions += int(parts[0])
            deletions += int(parts[1])
        except ValueError:
            continue
        files += 1
    metrics = {
        "meaningful_changed_lines": additions + deletions,
        "files_changed": files,
        "base": "HEAD^",
        "head": "HEAD",
    }
    return {
        "producer": "sample change-scope producer",
        "status": "passed",
        "evidence": [json.dumps(metrics, sort_keys=True)],
    }


def main() -> int:
    result = subprocess.run(
        ["python3", "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"],
        cwd=ROOT,
        text=True,
    )
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    checks = {
        "unit-tests": {
            "producer": "sample unit-test producer",
            "status": "passed" if result.returncode == 0 else "failed",
            "evidence": [
                "command: python3 -m unittest discover -s . -p test_*.py",
                f"revision: {revision}",
            ],
        },
        "build": run_check(
            "build",
            "sample Python build producer",
            ["python3", "-m", "compileall", "-q", "app.py", "test_app.py", "tools", ".guardrails"],
        ),
        "repository-validation": run_check(
            "repository-validation",
            "sample repository validation producer",
            ["python3", "tools/validate_demo.py"],
        ),
        "documentation": run_check(
            "documentation",
            "sample documentation validation producer",
            ["python3", "tools/validate_demo.py", "--documentation"],
        ),
        "change-scope": change_scope_check(),
    }
    evidence = {
        "version": 1,
        "subject": {"type": "git-commit", "revision": revision},
        "checks": checks,
    }
    output = EVIDENCE_DIR.parent / "evidence.json"
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    for check_id, check in checks.items():
        (EVIDENCE_DIR / f"{check_id}.json").write_text(
            json.dumps({"version": 1, "subject": evidence["subject"], "checks": {check_id: check}}, indent=2) + "\n"
        )
    print(f"Evidence: {output}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
