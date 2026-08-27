from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[3]
HELPER = SKILLS_ROOT / "issue-operator" / "scripts" / "gh_issue_helper.py"
STATE_SCRIPT = SKILLS_ROOT / "_shared-project-ops" / "scripts" / "project_ops_state.py"


class GhIssueHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.findings_path = self.root / "project-audit-findings.md"
        self.report_path = self.root / "full-test-suite-report.md"
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        self.gh_state = self.root / "gh-state.json"
        self.gh_state.write_text(json.dumps({"next_number": 1, "issues": [], "commands": []}), encoding="utf-8")
        self._write_fake_gh()

        env = os.environ.copy()
        env["PATH"] = f"{self.fake_bin}:{env['PATH']}"
        env["FAKE_GH_STATE"] = str(self.gh_state)
        self.env = env

        subprocess.run(
            [
                "python3",
                str(STATE_SCRIPT),
                "init-findings",
                "--path",
                str(self.findings_path),
                "--audit-date",
                "2026-03-12 10:00 EDT",
                "--scope",
                "repo-wide",
                "--branch",
                "codex/test",
                "--github-sync",
                "available",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )
        subprocess.run(
            [
                "python3",
                str(STATE_SCRIPT),
                "init-report",
                "--path",
                str(self.report_path),
                "--mode",
                "default",
                "--profile",
                "core",
                "--scope",
                "repo-wide",
                "--branch",
                "codex/test",
                "--dirty-worktree",
                "no",
                "--github-sync",
                "available",
                "--updated-at",
                "2026-03-12 10:00 EDT",
                "--skills",
                "issue-operator",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_fake_gh(self) -> None:
        script = self.fake_bin / "gh"
        script.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys
                from pathlib import Path

                state_path = Path(os.environ["FAKE_GH_STATE"])
                state = json.loads(state_path.read_text())
                args = sys.argv[1:]
                state["commands"].append(args)

                def save():
                    state_path.write_text(json.dumps(state))

                def issue_by_number(number):
                    for issue in state["issues"]:
                        if issue["number"] == number:
                            return issue
                    raise SystemExit(1)

                def get_opt(name, default=None):
                    if name not in args:
                        return default
                    return args[args.index(name) + 1]

                if args[:2] == ["issue", "list"]:
                    search = get_opt("--search", "")
                    filtered = [issue for issue in state["issues"] if search.replace('"', "").replace(" in:title", "") in issue["title"]]
                    print(json.dumps(filtered))
                    save()
                    raise SystemExit(0)

                if args[:2] == ["issue", "view"]:
                    number = int(args[2])
                    print(json.dumps(issue_by_number(number)))
                    save()
                    raise SystemExit(0)

                if args[:2] == ["issue", "create"]:
                    title = get_opt("--title", "")
                    body = get_opt("--body", "")
                    number = state["next_number"]
                    state["next_number"] += 1
                    issue = {
                        "number": number,
                        "title": title,
                        "body": body,
                        "state": "OPEN",
                        "url": f"https://example.test/issues/{number}",
                        "comments": [],
                    }
                    state["issues"].append(issue)
                    print(issue["url"])
                    save()
                    raise SystemExit(0)

                if args[:2] == ["issue", "edit"]:
                    number = int(args[2])
                    issue = issue_by_number(number)
                    issue["title"] = get_opt("--title", issue["title"])
                    issue["body"] = get_opt("--body", issue["body"])
                    save()
                    raise SystemExit(0)

                if args[:2] == ["issue", "reopen"]:
                    number = int(args[2])
                    issue_by_number(number)["state"] = "OPEN"
                    save()
                    raise SystemExit(0)

                if args[:2] == ["issue", "comment"]:
                    number = int(args[2])
                    issue_by_number(number)["comments"].append(get_opt("--body", ""))
                    save()
                    raise SystemExit(0)

                if args[:2] == ["issue", "close"]:
                    number = int(args[2])
                    issue_by_number(number)["state"] = "CLOSED"
                    save()
                    raise SystemExit(0)

                save()
                raise SystemExit(1)
                """
            ),
            encoding="utf-8",
        )
        script.chmod(0o755)

    def _read_state(self) -> dict:
        return json.loads(self.gh_state.read_text(encoding="utf-8"))

    def test_sync_creates_issue_and_updates_finding_and_report(self) -> None:
        subprocess.run(
            [
                "python3",
                str(STATE_SCRIPT),
                "upsert-finding",
                "--path",
                str(self.findings_path),
                "--payload",
                json.dumps(
                    {
                        "id": "BUG-001",
                        "title": "Claim flow crashes",
                        "type": "bug",
                        "severity": "high",
                        "surface": "App/Services/ExampleBackendClient.swift",
                        "evidence": ["Static mismatch confirmed."],
                        "impact": ["Claim redemption fails."],
                        "fix_plan": ["Align issue operator helper test."],
                    }
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )

        result = subprocess.run(
            [
                "python3",
                str(HELPER),
                "sync",
                "--repo-root",
                str(self.root),
                "--findings-path",
                str(self.findings_path),
                "--report-path",
                str(self.report_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["created"], ["#1"])

        findings_text = self.findings_path.read_text(encoding="utf-8")
        report_text = self.report_path.read_text(encoding="utf-8")
        self.assertIn("- GitHub Issue: #1", findings_text)
        self.assertIn("- Created: #1", report_text)

    def test_sync_updates_and_closes_resolved_issue_with_verification(self) -> None:
        state = self._read_state()
        state["issues"].append(
            {
                "number": 1,
                "title": "[BUG-001][bug][high] Old title",
                "body": "old body",
                "state": "OPEN",
                "url": "https://example.test/issues/1",
                "comments": [],
            }
        )
        self.gh_state.write_text(json.dumps(state), encoding="utf-8")

        subprocess.run(
            [
                "python3",
                str(STATE_SCRIPT),
                "upsert-finding",
                "--path",
                str(self.findings_path),
                "--payload",
                json.dumps(
                    {
                        "id": "BUG-001",
                        "title": "Claim flow crashes",
                        "type": "bug",
                        "severity": "high",
                        "status": "resolved",
                        "github_issue": "#1",
                        "verification": ["xcodebuild focused test passed"],
                        "resolution_notes": ["Aligned the claim response model."],
                    }
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )

        result = subprocess.run(
            [
                "python3",
                str(HELPER),
                "sync",
                "--repo-root",
                str(self.root),
                "--findings-path",
                str(self.findings_path),
                "--report-path",
                str(self.report_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["updated"], ["#1"])
        self.assertEqual(payload["closed"], ["#1"])

        state = self._read_state()
        self.assertEqual(state["issues"][0]["state"], "CLOSED")
        self.assertEqual(len(state["issues"][0]["comments"]), 1)

    def test_sync_does_not_close_resolved_issue_without_verification(self) -> None:
        state = self._read_state()
        state["issues"].append(
            {
                "number": 1,
                "title": "[BUG-001][bug][high] Claim flow crashes",
                "body": "body",
                "state": "OPEN",
                "url": "https://example.test/issues/1",
                "comments": [],
            }
        )
        self.gh_state.write_text(json.dumps(state), encoding="utf-8")

        subprocess.run(
            [
                "python3",
                str(STATE_SCRIPT),
                "upsert-finding",
                "--path",
                str(self.findings_path),
                "--payload",
                json.dumps(
                    {
                        "id": "BUG-001",
                        "title": "Claim flow crashes",
                        "type": "bug",
                        "severity": "high",
                        "status": "resolved",
                        "github_issue": "#1",
                    }
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )

        result = subprocess.run(
            [
                "python3",
                str(HELPER),
                "sync",
                "--repo-root",
                str(self.root),
                "--findings-path",
                str(self.findings_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )
        payload = json.loads(result.stdout)
        self.assertIn("BUG-001: missing verification; issue left open", payload["skipped"])

        state = self._read_state()
        self.assertEqual(state["issues"][0]["state"], "OPEN")


if __name__ == "__main__":
    unittest.main()
