#!/usr/bin/env python3
"""Sync confirmed findings with GitHub issues through gh."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SHARED_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "_shared-project-ops" / "scripts"
if str(SHARED_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_SCRIPTS_DIR))

from project_ops_state import load_findings, load_report, save_findings, save_report  # noqa: E402

ACTIONABLE_STATUSES = {"confirmed-open", "in-progress", "resolved"}


@dataclass
class SyncResult:
    created: list[str]
    updated: list[str]
    closed: list[str]
    reopened: list[str]
    skipped: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "closed": self.closed,
            "reopened": self.reopened,
            "skipped": self.skipped,
            "errors": self.errors,
        }


def run_gh(gh_binary: str, repo_root: Path, repo: str | None, args: list[str]) -> subprocess.CompletedProcess[str]:
    command = [gh_binary, *args]
    if repo:
        command.extend(["--repo", repo])
    return subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def gh_json(gh_binary: str, repo_root: Path, repo: str | None, args: list[str]) -> Any:
    result = run_gh(gh_binary, repo_root, repo, args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh command failed")
    output = result.stdout.strip()
    return json.loads(output) if output else None


def issue_title(finding: Any) -> str:
    return f"[{finding.finding_id}][{finding.finding_type}][{finding.severity}] {finding.title}"


def issue_body(finding: Any) -> str:
    def block(title: str, items: list[str]) -> list[str]:
        section = [title]
        for item in items or ["none"]:
            section.append(f"- {item}")
        section.append("")
        return section

    lines = [
        "Summary",
        f"- Finding: {finding.title}",
        f"- Surface: {finding.surface or 'none'}",
        f"- Severity: {finding.severity}",
        "",
    ]
    lines.extend(block("Evidence", finding.evidence))
    lines.extend(block("Impact", finding.impact))
    lines.extend(block("Fix plan", finding.fix_plan))
    lines.extend(block("Verification", finding.verification))
    return "\n".join(lines).strip()


def close_comment(finding: Any) -> str:
    changed = finding.resolution_notes or ["Resolved in local changes."]
    verification = finding.verification or ["No verification recorded."]
    notes = []
    if any(item for item in finding.evidence):
        notes.append("Evidence rechecked against the current findings log.")
    if finding.status != "resolved":
        notes.append(f"Finding status is {finding.status}.")
    if not notes:
        notes.append("No residual risk recorded.")

    lines = ["Resolved from the tracked finding entry.", "", "What changed"]
    lines.extend(f"- {item}" for item in changed)
    lines.extend(["", "Verification"])
    lines.extend(f"- {item}" for item in verification)
    lines.extend(["", "Notes"])
    lines.extend(f"- {item}" for item in notes)
    return "\n".join(lines)


def parse_issue_number(value: str) -> int | None:
    match = re.search(r"(\d+)$", value.strip())
    return int(match.group(1)) if match else None


def lookup_issue(
    gh_binary: str,
    repo_root: Path,
    repo: str | None,
    finding: Any,
) -> dict[str, Any] | None:
    if finding.github_issue and finding.github_issue != "none":
        number = parse_issue_number(finding.github_issue)
        if number is not None:
            try:
                issue = gh_json(
                    gh_binary,
                    repo_root,
                    repo,
                    ["issue", "view", str(number), "--json", "number,title,state,url,body"],
                )
                if issue:
                    return issue
            except RuntimeError:
                pass

    search_query = f'"{finding.finding_id}" in:title'
    issues = gh_json(
        gh_binary,
        repo_root,
        repo,
        ["issue", "list", "--state", "all", "--limit", "20", "--search", search_query, "--json", "number,title,state,url,body"],
    )
    preferred_prefix = f"[{finding.finding_id}]"
    for issue in issues or []:
        if issue.get("title", "").startswith(preferred_prefix):
            return issue
    for issue in issues or []:
        if finding.finding_id in issue.get("title", ""):
            return issue
    return None


def create_issue(
    gh_binary: str,
    repo_root: Path,
    repo: str | None,
    finding: Any,
) -> dict[str, Any]:
    title = issue_title(finding)
    body = issue_body(finding)
    result = run_gh(
        gh_binary,
        repo_root,
        repo,
        ["issue", "create", "--title", title, "--body", body],
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue create failed")
    created = lookup_issue(gh_binary, repo_root, repo, finding)
    if created is None:
        number = parse_issue_number(result.stdout)
        if number is None:
            raise RuntimeError("Could not determine created issue number.")
        created = gh_json(
            gh_binary,
            repo_root,
            repo,
            ["issue", "view", str(number), "--json", "number,title,state,url,body"],
        )
    return created


def update_issue(
    gh_binary: str,
    repo_root: Path,
    repo: str | None,
    issue: dict[str, Any],
    finding: Any,
) -> bool:
    title = issue_title(finding)
    body = issue_body(finding)
    changed = issue.get("title") != title or issue.get("body") != body
    if changed:
        result = run_gh(
            gh_binary,
            repo_root,
            repo,
            ["issue", "edit", str(issue["number"]), "--title", title, "--body", body],
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue edit failed")
    if finding.status in {"confirmed-open", "in-progress"} and issue.get("state") == "CLOSED":
        result = run_gh(gh_binary, repo_root, repo, ["issue", "reopen", str(issue["number"])])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue reopen failed")
        return True
    return changed


def close_issue(
    gh_binary: str,
    repo_root: Path,
    repo: str | None,
    issue: dict[str, Any],
    finding: Any,
) -> bool:
    if issue.get("state") == "CLOSED":
        return False
    result = run_gh(
        gh_binary,
        repo_root,
        repo,
        ["issue", "comment", str(issue["number"]), "--body", close_comment(finding)],
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue comment failed")
    result = run_gh(gh_binary, repo_root, repo, ["issue", "close", str(issue["number"])])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue close failed")
    return True


def sync_findings(
    repo_root: Path,
    findings_path: Path,
    report_path: Path | None,
    repo: str | None,
    gh_binary: str,
    dry_run: bool,
) -> dict[str, Any]:
    findings = load_findings(findings_path)
    result = SyncResult(created=[], updated=[], closed=[], reopened=[], skipped=[], errors=[])

    if shutil.which(gh_binary) is None:
        return {"available": False, **result.to_dict(), "message": f"`{gh_binary}` not found in PATH."}

    actionable = [finding for finding in findings.findings if finding.status in ACTIONABLE_STATUSES]
    for finding in actionable:
        try:
            issue = lookup_issue(gh_binary, repo_root, repo, finding)
            if issue is None and finding.status == "resolved":
                result.skipped.append(f"{finding.finding_id}: resolved finding has no matching issue")
                continue

            if finding.status in {"confirmed-open", "in-progress"}:
                if issue is None:
                    if dry_run:
                        result.created.append(f"{finding.finding_id}:dry-run")
                        continue
                    issue = create_issue(gh_binary, repo_root, repo, finding)
                    finding.github_issue = f"#{issue['number']}"
                    result.created.append(f"#{issue['number']}")
                else:
                    changed_or_reopened = update_issue(gh_binary, repo_root, repo, issue, finding) if not dry_run else False
                    finding.github_issue = f"#{issue['number']}"
                    if issue.get("state") == "CLOSED" and not dry_run:
                        result.reopened.append(f"#{issue['number']}")
                    if changed_or_reopened and f"#{issue['number']}" not in result.updated:
                        result.updated.append(f"#{issue['number']}")
                    if not changed_or_reopened:
                        result.skipped.append(f"{finding.finding_id}: issue already in sync")
                continue

            if finding.status == "resolved":
                if not finding.verification:
                    result.skipped.append(f"{finding.finding_id}: missing verification; issue left open")
                    continue
                if issue is None:
                    result.skipped.append(f"{finding.finding_id}: resolved finding has no matching issue")
                    continue
                if dry_run:
                    result.closed.append(f"#{issue['number']}:dry-run")
                    continue
                finding.github_issue = f"#{issue['number']}"
                if issue.get("title") != issue_title(finding) or issue.get("body") != issue_body(finding):
                    update_issue(gh_binary, repo_root, repo, issue, finding)
                    if f"#{issue['number']}" not in result.updated:
                        result.updated.append(f"#{issue['number']}")
                if close_issue(gh_binary, repo_root, repo, issue, finding):
                    result.closed.append(f"#{issue['number']}")
                else:
                    result.skipped.append(f"{finding.finding_id}: issue already closed")
        except RuntimeError as error:
            result.errors.append(f"{finding.finding_id}: {error}")

    if not dry_run:
        save_findings(findings_path, findings)
        if report_path is not None:
            report = load_report(report_path)
            for issue_id in result.created:
                report.add_issue_activity("Created", issue_id)
            for issue_id in result.updated:
                report.add_issue_activity("Updated", issue_id)
            for issue_id in result.closed:
                report.add_issue_activity("Closed", issue_id)
            save_report(report_path, report)

    return {"available": True, **result.to_dict()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_cmd = subparsers.add_parser("sync")
    sync_cmd.add_argument("--repo-root", required=True)
    sync_cmd.add_argument("--findings-path", required=True)
    sync_cmd.add_argument("--report-path")
    sync_cmd.add_argument("--repo")
    sync_cmd.add_argument("--gh-binary", default="gh")
    sync_cmd.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sync":
        result = sync_findings(
            repo_root=Path(args.repo_root),
            findings_path=Path(args.findings_path),
            report_path=Path(args.report_path) if args.report_path else None,
            repo=args.repo,
            gh_binary=args.gh_binary,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
