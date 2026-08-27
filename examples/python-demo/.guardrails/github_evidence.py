#!/usr/bin/env python3
"""Collect revision-bound producer status from GitHub Checks.

This is deliberately provider-neutral: GitHub exposes the producer result, while
the producer remains responsible for uploading its detailed evidence artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CONCLUSIONS = {
    "success": "passed",
    "neutral": "passed",
    "failure": "failed",
    "cancelled": "blocked",
    "timed_out": "blocked",
    "action_required": "blocked",
    "stale": "blocked",
    "skipped": "not_run",
}


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("version") != 1 or not isinstance(manifest.get("producers"), list):
        raise ValueError("producer manifest must contain version 1 and a producers list")
    controls: set[str] = set()
    check_names: set[str] = set()
    for producer in manifest["producers"]:
        if not isinstance(producer, dict):
            raise ValueError("producer manifest entries must be objects")
        required = {"control_id", "check_name", "workflow"}
        if not required.issubset(producer):
            raise ValueError("producer manifest entry is missing a required field")
        control_id = producer["control_id"]
        check_name = producer["check_name"]
        if control_id in controls or check_name in check_names:
            raise ValueError("producer manifest contains a duplicate control or check")
        if not all(isinstance(item, str) and item.strip() for item in (control_id, check_name, producer["workflow"])):
            raise ValueError("producer manifest fields must be non-empty strings")
        if "wait_for" in producer and not isinstance(producer["wait_for"], bool):
            raise ValueError("producer manifest wait_for must be boolean when provided")
        controls.add(control_id)
        check_names.add(check_name)


def check_run_evidence(control_id: str, check: dict[str, Any]) -> dict[str, Any]:
    """Convert one GitHub check run into the shared evidence vocabulary."""
    conclusion = check.get("conclusion") or "in_progress"
    status = CONCLUSIONS.get(conclusion, "not_run")
    url = check.get("html_url") or check.get("details_url") or "unavailable"
    record = f"{check.get('name', control_id)}: {conclusion}; {url}"
    result: dict[str, Any] = {
        "producer": f"GitHub Check: {check.get('name', control_id)}",
        "status": status,
        "evidence": [record],
    }
    if status in {"blocked", "not_run"}:
        result["reason"] = (
            f"GitHub check concluded {conclusion}; producer did not return a passing result."
        )
    return result


def _request(url: str, token: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def collect_checks(repo: str, revision: str, token: str, manifest: dict[str, Any], wait_seconds: int = 0) -> dict[str, Any]:
    validate_manifest(manifest)
    checks_url = f"https://api.github.com/repos/{repo}/commits/{revision}/check-runs?per_page=100"
    deadline = time.monotonic() + max(0, wait_seconds)
    check_runs: list[dict[str, Any]] = []
    while True:
        payload = _request(checks_url, token)
        check_runs = payload.get("check_runs", [])
        names = {item.get("name") for item in check_runs}
        required = {
            item["check_name"]
            for item in manifest["producers"]
            if item.get("wait_for", True)
        }
        all_expected = {item["check_name"] for item in manifest["producers"]}
        required_runs = [item for item in check_runs if item.get("name") in required]
        active_optional = [
            item for item in check_runs
            if item.get("name") in all_expected
            and item.get("name") not in required
            and item.get("status") != "completed"
        ]
        complete = required.issubset(names) and all(
            item.get("status") == "completed" for item in required_runs
        ) and not active_optional
        if complete or time.monotonic() >= deadline:
            break
        time.sleep(10)

    by_name: dict[str, dict[str, Any]] = {}
    for check in check_runs:
        name = check.get("name")
        if name:
            by_name[name] = check

    checks: dict[str, Any] = {}
    for producer in manifest["producers"]:
        control_id = producer["control_id"]
        check = by_name.get(producer["check_name"])
        if check is None:
            checks[control_id] = {
                "producer": f"GitHub Check: {producer['check_name']}",
                "status": "not_run",
                "reason": "The configured producer check did not report this revision.",
            }
        else:
            checks[control_id] = check_run_evidence(control_id, check)
    return {
        "version": 1,
        "subject": {"type": "git-commit", "revision": revision},
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect GitHub producer check evidence")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--revision", required=True)
    parser.add_argument("--token", default=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wait-seconds", type=int, default=0)
    args = parser.parse_args()
    if not args.repo or not args.token:
        print("ERROR --repo and --token are required", file=sys.stderr)
        return 2
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        evidence = collect_checks(args.repo, args.revision, args.token, manifest, args.wait_seconds)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2))
        return 0
    except (OSError, ValueError, KeyError, HTTPError, URLError) as error:
        print(f"ERROR collecting GitHub evidence: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
