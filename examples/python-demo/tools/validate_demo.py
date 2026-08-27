#!/usr/bin/env python3
"""Validate the sample repository's local contracts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MACHINE_PATH = re.compile(
    rf"(/{'Users'}/|/{'private'}/|\\\\{'Users'}\\\\)"
)


def fail_if(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--documentation", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []

    required = ("README.md", "AGENTS.md", "app.py", "test_app.py", ".ai/guardrails.yaml", ".ai/control-catalog.yaml")
    for relative in required:
        fail_if(not (ROOT / relative).is_file(), f"missing required file: {relative}", failures)

    try:
        policy = json.loads((ROOT / ".ai/guardrails.yaml").read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / ".ai/control-catalog.yaml").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"policy/catalog is not valid JSON-compatible YAML: {error}")
        policy = {}
        catalog = {}

    control_ids = {
        control.get("id")
        for control in catalog.get("controls", [])
        if isinstance(control, dict)
    }
    selected = {
        control_id
        for operation in policy.get("operations", {}).values()
        for enforcement in ("required", "advisory")
        for control_id in operation.get(enforcement, [])
    }
    fail_if(not selected <= control_ids, "policy selects controls absent from catalog", failures)

    tracked_text = subprocess.run(
        ["git", "ls-files", "*.md", "*.py", "*.yaml", "*.yml"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for relative in tracked_text:
        if relative == "tools/validate_demo.py":
            continue
        # A removed tracked file is intentionally absent from the working tree;
        # validate the files that will actually be shipped.
        if not (ROOT / relative).is_file():
            continue
        content = (ROOT / relative).read_text(encoding="utf-8")
        fail_if(bool(MACHINE_PATH.search(content)), f"machine-local path found in {relative}", failures)

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT)
    fail_if(diff_check.returncode != 0, "git diff --check failed", failures)

    if args.documentation:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        fail_if("## Run the example" not in readme, "README is missing the run instructions", failures)
        fail_if("repository-specific ground truth" not in readme, "README does not explain repository ground truth", failures)
        fail_if(not agents.strip(), "AGENTS.md is empty", failures)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Demo repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
