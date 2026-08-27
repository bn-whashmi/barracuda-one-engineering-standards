from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[3]
RUNNER = SKILLS_ROOT / "full-test-suite" / "scripts" / "full_test_suite_runner.py"
STATE_SCRIPT = SKILLS_ROOT / "_shared-project-ops" / "scripts" / "project_ops_state.py"


class FullTestSuiteRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        subprocess.run(["git", "-C", str(self.root), "init"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "checkout", "-b", "codex/test-suite"], check=True, capture_output=True)
        (self.root / "README.md").write_text("# Test repo\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "README.md"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.name=Codex", "-c", "user.email=codex@example.com", "commit", "-m", "init"],
            check=True,
            capture_output=True,
        )
        self.findings_path = self.root / "project-audit-findings.md"
        self.report_path = self.root / "full-test-suite-report.md"
        self.manifest_path = self.root / "full-test-suite-manifest.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, *args: str) -> dict:
        result = subprocess.run(
            ["python3", str(RUNNER), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def _state(self, *args: str, payload: dict | None = None) -> dict:
        command = ["python3", str(STATE_SCRIPT), *args]
        if payload is not None:
            command.extend(["--payload", json.dumps(payload)])
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def _init(self, profile: str = "core") -> dict:
        return self._run(
            "init",
            "--repo-root",
            str(self.root),
            "--findings-path",
            str(self.findings_path),
            "--report-path",
            str(self.report_path),
            "--manifest-path",
            str(self.manifest_path),
            "--scope",
            "repo-wide",
            "--profile",
            profile,
        )

    def _complete_current_cycle(self) -> None:
        while True:
            action = self._run("next-action", "--manifest-path", str(self.manifest_path))
            if action["action"] != "run-skill":
                return
            self._run(
                "record-skill",
                "--report-path",
                str(self.report_path),
                "--manifest-path",
                str(self.manifest_path),
                "--skill",
                action["skill"],
                "--status",
                "completed",
            )

    def test_init_creates_manifest_and_first_pending_skill(self) -> None:
        payload = self._init(profile="pre-release")
        self.assertEqual(payload["next_action"]["action"], "run-skill")
        self.assertEqual(payload["next_action"]["skill"], "project-health-check")

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["selected_skills"][0], "project-health-check")
        self.assertIn("release-readiness", manifest["selected_skills"])

    def test_record_skill_advances_through_cycle(self) -> None:
        self._init()

        first = self._run("next-action", "--manifest-path", str(self.manifest_path))
        self.assertEqual(first["skill"], "project-health-check")
        result = self._run(
            "record-skill",
            "--report-path",
            str(self.report_path),
            "--manifest-path",
            str(self.manifest_path),
            "--skill",
            "project-health-check",
            "--status",
            "completed",
        )
        self.assertEqual(result["next_action"]["action"], "run-skill")
        self.assertEqual(result["next_action"]["skill"], "bug-hunter")

    def test_init_with_reset_artifacts_archives_existing_generated_state(self) -> None:
        self.findings_path.write_text("# stale findings\n", encoding="utf-8")
        self.report_path.write_text("# stale report\n", encoding="utf-8")
        self.manifest_path.write_text('{"status":"stale"}\n', encoding="utf-8")

        payload = self._run(
            "init",
            "--repo-root",
            str(self.root),
            "--findings-path",
            str(self.findings_path),
            "--report-path",
            str(self.report_path),
            "--manifest-path",
            str(self.manifest_path),
            "--scope",
            "repo-wide",
            "--reset-artifacts",
        )

        archived = payload["archived_artifacts"]
        self.assertIn("findings", archived)
        self.assertIn("report", archived)
        self.assertIn("manifest", archived)
        self.assertTrue(Path(archived["findings"]).exists())
        self.assertTrue(Path(archived["report"]).exists())
        self.assertTrue(Path(archived["manifest"]).exists())

        findings_text = self.findings_path.read_text(encoding="utf-8")
        report_text = self.report_path.read_text(encoding="utf-8")
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertIn("# Project Audit Findings", findings_text)
        self.assertIn("# Full Test Suite Report", report_text)
        self.assertEqual(manifest["status"], "active")

    def test_plan_fixes_outputs_sorted_queue_and_updates_report(self) -> None:
        self._init()
        self._state(
            "upsert-finding",
            "--path",
            str(self.findings_path),
            payload={"id": "DOC-001", "title": "Doc drift", "type": "docs", "severity": "medium"},
        )
        self._state(
            "upsert-finding",
            "--path",
            str(self.findings_path),
            payload={"id": "SEC-001", "title": "Auth bypass", "type": "security", "severity": "high"},
        )

        payload = self._run(
            "plan-fixes",
            "--findings-path",
            str(self.findings_path),
            "--report-path",
            str(self.report_path),
        )
        self.assertEqual([item["id"] for item in payload["queue"]], ["SEC-001", "DOC-001"])
        report_text = self.report_path.read_text(encoding="utf-8")
        self.assertIn("- SEC-001 [high/security] - Auth bypass", report_text)

    def test_suggest_rerun_maps_api_and_config_surfaces_to_relevant_skills(self) -> None:
        payload = self._run(
            "suggest-rerun",
            "--profile",
            "deep-audit",
            "--surfaces",
            "services/pbrotator-api/src/routes/share.ts,services/pbrotator-api/src/env.ts",
            "--types",
            "api-contract,config",
        )
        self.assertEqual(
            payload["skills"],
            ["api-contract-auditor", "config-drift-auditor", "security-audit-lite", "project-health-check", "issue-operator"],
        )

    def test_manifest_loop_converges_after_fix_rerun_and_clean_rescan(self) -> None:
        self._init()
        self._state(
            "upsert-finding",
            "--path",
            str(self.findings_path),
            payload={"id": "BUG-001", "title": "Crash", "type": "bug", "severity": "high"},
        )

        self._complete_current_cycle()
        self._run(
            "record-issue-sync",
            "--manifest-path",
            str(self.manifest_path),
            "--payload",
            json.dumps({"created": [], "updated": [], "closed": [], "skipped": [], "errors": [], "available": False}),
        )

        action = self._run("next-action", "--manifest-path", str(self.manifest_path))
        self.assertEqual(action["action"], "fix-finding")
        self.assertEqual(action["finding"]["id"], "BUG-001")

        self._state(
            "upsert-finding",
            "--path",
            str(self.findings_path),
            payload={
                "id": "BUG-001",
                "status": "resolved",
                "verification": ["Focused regression test passed."],
                "resolution_notes": ["Fixed the crash and added a regression test."],
            },
        )
        fix_result = self._run(
            "record-fix",
            "--manifest-path",
            str(self.manifest_path),
            "--finding-id",
            "BUG-001",
            "--surfaces",
            "App/Services/ExampleBackendClient.swift",
            "--types",
            "bug",
        )
        self.assertEqual(fix_result["next_action"]["action"], "run-skill")
        self.assertEqual(fix_result["next_action"]["cycle_kind"], "rerun")

        self._complete_current_cycle()
        self._run(
            "record-issue-sync",
            "--manifest-path",
            str(self.manifest_path),
            "--payload",
            json.dumps({"created": [], "updated": [], "closed": [], "skipped": [], "errors": [], "available": False}),
        )

        action = self._run("next-action", "--manifest-path", str(self.manifest_path))
        self.assertEqual(action["action"], "run-skill")
        self.assertEqual(action["cycle_kind"], "full-scan")

        self._complete_current_cycle()
        self._run(
            "record-issue-sync",
            "--manifest-path",
            str(self.manifest_path),
            "--payload",
            json.dumps({"created": [], "updated": [], "closed": [], "skipped": [], "errors": [], "available": False}),
        )

        action = self._run("next-action", "--manifest-path", str(self.manifest_path))
        self.assertEqual(action["action"], "finalize")

    def test_finalize_syncs_counts_remaining_items_and_marks_manifest_complete(self) -> None:
        self._init()
        self._state(
            "upsert-finding",
            "--path",
            str(self.findings_path),
            payload={"id": "BUG-001", "title": "Crash", "type": "bug", "severity": "high", "status": "resolved"},
        )
        self._state(
            "upsert-finding",
            "--path",
            str(self.findings_path),
            payload={"id": "DOC-001", "title": "Blocked docs", "type": "docs", "status": "blocked"},
        )
        payload = self._run(
            "finalize",
            "--repo-root",
            str(self.root),
            "--findings-path",
            str(self.findings_path),
            "--report-path",
            str(self.report_path),
            "--manifest-path",
            str(self.manifest_path),
        )
        self.assertEqual(payload["final_state"], "no confirmed-open findings; blocked or needs-context items remain")
        report_text = self.report_path.read_text(encoding="utf-8")
        self.assertIn("- Resolved findings: 1", report_text)
        self.assertIn("- Blocked findings: 1", report_text)
        self.assertIn("- DOC-001 (blocked) - Blocked docs", report_text)

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "completed")


if __name__ == "__main__":
    unittest.main()
