from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SHARED_SCRIPTS = Path(__file__).resolve().parents[1]
if str(SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SHARED_SCRIPTS))

from project_ops_state import (
    load_findings,
    load_report,
    save_findings,
    save_report,
    sync_report_from_findings,
)


class ProjectOpsStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.findings_path = self.root / "project-audit-findings.md"
        self.report_path = self.root / "full-test-suite-report.md"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_findings_upsert_updates_in_place_and_preserves_order(self) -> None:
        document = load_findings(self.findings_path)
        document.summary.update(
            {
                "Audit date": "2026-03-12 10:00 EDT",
                "Scope": "repo-wide",
                "Branch": "codex/test",
                "GitHub issue sync": "available",
            }
        )
        document.upsert_finding(
            {
                "id": "BUG-001",
                "title": "Redeem flow decodes the wrong shape",
                "severity": "high",
                "surface": "App/Services/ExampleBackendClient.swift",
                "evidence": ["Static decode mismatch between backend and client."],
            }
        )
        document.upsert_finding(
            {
                "id": "BUG-001",
                "status": "resolved",
                "verification": ["Focused regression test passed."],
                "resolution_notes": ["Claim redemption now decodes the shared contract."],
            }
        )
        save_findings(self.findings_path, document)

        reloaded = load_findings(self.findings_path)
        self.assertEqual(len(reloaded.findings), 1)
        finding = reloaded.findings[0]
        self.assertEqual(finding.status, "resolved")
        self.assertEqual(finding.title, "Redeem flow decodes the wrong shape")
        self.assertEqual(finding.verification, ["Focused regression test passed."])

    def test_merge_findings_combines_evidence_and_removes_duplicate(self) -> None:
        document = load_findings(self.findings_path)
        document.summary.update(
            {
                "Audit date": "2026-03-12 10:00 EDT",
                "Scope": "repo-wide",
                "Branch": "codex/test",
                "GitHub issue sync": "available",
            }
        )
        document.upsert_finding(
            {
                "id": "BUG-001",
                "title": "Root cause",
                "evidence": ["Bug evidence"],
            }
        )
        document.upsert_finding(
            {
                "id": "SEC-001",
                "title": "Duplicate root cause",
                "severity": "high",
                "evidence": ["Security angle"],
            }
        )
        document.merge_findings("BUG-001", "SEC-001")
        save_findings(self.findings_path, document)

        reloaded = load_findings(self.findings_path)
        self.assertEqual([finding.finding_id for finding in reloaded.findings], ["BUG-001"])
        self.assertIn("Security angle", reloaded.findings[0].evidence)
        self.assertIn("Merged duplicate finding SEC-001.", reloaded.findings[0].resolution_notes)

    def test_fix_queue_prioritizes_severity_then_type(self) -> None:
        document = load_findings(self.findings_path)
        document.summary.update(
            {
                "Audit date": "2026-03-12 10:00 EDT",
                "Scope": "repo-wide",
                "Branch": "codex/test",
                "GitHub issue sync": "available",
            }
        )
        document.upsert_finding({"id": "DOC-001", "title": "Doc drift", "type": "docs", "severity": "medium"})
        document.upsert_finding({"id": "SEC-001", "title": "Auth bypass", "type": "security", "severity": "high"})
        document.upsert_finding({"id": "BUG-002", "title": "Crash", "type": "bug", "severity": "high"})
        queue = document.build_fix_queue(["confirmed-open"])

        self.assertEqual([item["id"] for item in queue], ["SEC-001", "BUG-002", "DOC-001"])

    def test_report_sync_reflects_findings_state_deterministically(self) -> None:
        findings = load_findings(self.findings_path)
        findings.summary.update(
            {
                "Audit date": "2026-03-12 10:00 EDT",
                "Scope": "repo-wide",
                "Branch": "codex/test",
                "GitHub issue sync": "available",
            }
        )
        findings.upsert_finding({"id": "BUG-001", "title": "Crash", "type": "bug", "severity": "high"})
        findings.upsert_finding({"id": "DOC-001", "title": "Doc drift", "type": "docs", "status": "blocked"})
        save_findings(self.findings_path, findings)

        report = load_report(self.report_path)
        report.summary.update(
            {
                "Mode": "default",
                "Profile": "core",
                "Scope": "repo-wide",
                "Branch": "codex/test",
                "Dirty worktree": "yes",
                "GitHub issue sync": "available",
                "Updated at": "2026-03-12 10:05 EDT",
            }
        )
        report.upsert_skill("bug-hunter", "completed")
        sync_report_from_findings(report, findings, "2026-03-12 10:05 EDT")
        save_report(self.report_path, report)

        text = self.report_path.read_text(encoding="utf-8")
        self.assertIn("- Confirmed-open findings: 1", text)
        self.assertIn("- Blocked findings: 1", text)
        self.assertIn("- BUG-001 [high/bug] - Crash", text)
        self.assertIn("- DOC-001 (blocked) - Doc drift", text)


if __name__ == "__main__":
    unittest.main()
