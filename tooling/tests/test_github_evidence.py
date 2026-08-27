from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "github_evidence.py"
SPEC = importlib.util.spec_from_file_location("agentic_github_evidence", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CheckRunEvidenceTests(unittest.TestCase):
    def test_successful_check_is_passed(self) -> None:
        result = MODULE.check_run_evidence(
            "unit-tests",
            {
                "name": "Unit Tests",
                "status": "completed",
                "conclusion": "success",
                "html_url": "https://github.example/runs/1",
                "head_sha": "abc123",
            },
        )

        self.assertEqual(result["status"], "passed")
        self.assertIn("Unit Tests", result["evidence"][0])

    def test_skipped_check_is_not_run_with_reason(self) -> None:
        result = MODULE.check_run_evidence(
            "sonarqube",
            {
                "name": "SonarQube Quality Gate",
                "status": "completed",
                "conclusion": "skipped",
                "html_url": "https://github.example/runs/2",
                "head_sha": "abc123",
            },
        )

        self.assertEqual(result["status"], "not_run")
        self.assertIn("skipped", result["reason"])

    def test_failed_check_retains_evidence(self) -> None:
        result = MODULE.check_run_evidence(
            "dependency-review",
            {
                "name": "Dependency Review",
                "status": "completed",
                "conclusion": "failure",
                "html_url": "https://github.example/runs/3",
                "head_sha": "abc123",
            },
        )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["evidence"])

    def test_manifest_rejects_duplicate_controls(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            MODULE.validate_manifest(
                {
                    "version": 1,
                    "producers": [
                        {"control_id": "build", "check_name": "Build", "workflow": "Build"},
                        {"control_id": "build", "check_name": "Other", "workflow": "Other"},
                    ],
                }
            )

    def test_manifest_rejects_non_boolean_wait_for(self) -> None:
        with self.assertRaisesRegex(ValueError, "wait_for"):
            MODULE.validate_manifest(
                {
                    "version": 1,
                    "producers": [
                        {
                            "control_id": "build",
                            "check_name": "Build",
                            "workflow": "Build",
                            "wait_for": "yes",
                        }
                    ],
                }
            )

    def test_waits_for_optional_check_once_it_has_started(self) -> None:
        manifest = {
            "version": 1,
            "producers": [
                {"control_id": "build", "check_name": "Build", "workflow": "Build"},
                {
                    "control_id": "codeql-sast",
                    "check_name": "CodeQL",
                    "workflow": "CodeQL",
                    "wait_for": False,
                },
            ],
        }
        queued = {
            "check_runs": [
                {"name": "Build", "status": "completed", "conclusion": "success"},
                {"name": "CodeQL", "status": "in_progress", "conclusion": None},
            ]
        }
        completed = {
            "check_runs": [
                {"name": "Build", "status": "completed", "conclusion": "success"},
                {"name": "CodeQL", "status": "completed", "conclusion": "success"},
            ]
        }

        with patch.object(MODULE, "_request", side_effect=[queued, completed]) as request:
            with patch.object(MODULE.time, "monotonic", side_effect=[0, 1, 2]):
                with patch.object(MODULE.time, "sleep"):
                    evidence = MODULE.collect_checks(
                        "owner/repo", "abc123", "token", manifest, wait_seconds=30
                    )

        self.assertEqual(request.call_count, 2)
        self.assertEqual(evidence["checks"]["codeql-sast"]["status"], "passed")

    def test_uses_newest_check_when_github_returns_duplicate_names(self) -> None:
        manifest = {
            "version": 1,
            "producers": [
                {"control_id": "unit-tests", "check_name": "Unit Tests", "workflow": "Unit Tests"},
            ],
        }
        newest_first = {
            "check_runs": [
                {
                    "id": 2,
                    "name": "Unit Tests",
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-08-27T14:52:03Z",
                    "html_url": "https://github.example/runs/2",
                },
                {
                    "id": 1,
                    "name": "Unit Tests",
                    "status": "completed",
                    "conclusion": "cancelled",
                    "started_at": "2026-08-27T14:50:40Z",
                    "html_url": "https://github.example/runs/1",
                },
            ]
        }

        with patch.object(MODULE, "_request", return_value=newest_first):
            evidence = MODULE.collect_checks(
                "owner/repo", "abc123", "token", manifest, wait_seconds=0
            )

        self.assertEqual(evidence["checks"]["unit-tests"]["status"], "passed")
        self.assertIn("runs/2", evidence["checks"]["unit-tests"]["evidence"][0])


if __name__ == "__main__":
    unittest.main()
