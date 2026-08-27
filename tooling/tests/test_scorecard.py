from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "guardrail_scorecard.py"
SPEC = importlib.util.spec_from_file_location("guardrail_scorecard", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ScorecardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = {
            "version": 1,
            "name": "test",
            "operations": {
                "change": {"required": ["build"], "advisory": ["fossa"]}
            },
        }
        self.evidence = {
            "version": 1,
            "subject": {"type": "git-commit", "revision": "abc123"},
            "checks": {
                "build": {
                    "producer": "CI",
                    "status": "passed",
                    "evidence": ["job: build"],
                },
                "fossa": {
                    "producer": "FOSSA",
                    "status": "not_run",
                    "reason": "not configured",
                },
            },
        }
        self.catalog = {
            "version": 1,
            "controls": [
                {"id": "build", "activation": "github-native"},
                {"id": "fossa", "activation": "external"},
            ],
        }

    def test_reports_orange_for_advisory_gap(self) -> None:
        card = MODULE.scorecard(
            self.policy, self.evidence, "change", "abc123", catalog=self.catalog
        )
        self.assertEqual(card["status"], "ORANGE")
        self.assertEqual(card["decision"], "allow")
        self.assertEqual(card["enforced"]["percent"], 100.0)
        self.assertEqual(card["activation"]["external"], 1)
        self.assertEqual(card["readiness_status"], "ORANGE")
        self.assertEqual(card["readiness"]["ORANGE"], 1)
        fossa = next(control for control in card["controls"] if control["id"] == "fossa")
        self.assertEqual(fossa["enforcement"], "advisory")
        self.assertEqual(fossa["evidence_status"], "no_result")
        self.assertEqual(card["findings"][0]["status"], "no_result")
        self.assertNotIn("not_run", json.dumps(card))
        self.assertNotIn("required", json.dumps(card["findings"]))
        fossa = next(control for control in card["controls"] if control["id"] == "fossa")
        self.assertEqual(fossa["enforcement"], "advisory")
        self.assertEqual(fossa["evidence_status"], "no_result")
        self.assertEqual(card["findings"][0]["status"], "no_result")
        self.assertNotIn("not_run", json.dumps(card))
        self.assertNotIn("required", json.dumps(card["findings"]))

    def test_reports_red_for_required_gap(self) -> None:
        self.evidence["checks"]["build"]["status"] = "not_run"
        self.evidence["checks"]["build"].pop("evidence")
        self.evidence["checks"]["build"]["reason"] = "not configured"
        card = MODULE.scorecard(
            self.policy, self.evidence, "change", "abc123", catalog=self.catalog
        )
        self.assertEqual(card["status"], "RED")
        self.assertEqual(card["decision"], "block")

    def test_reports_green_when_all_findings_are_clear(self) -> None:
        self.evidence["checks"]["fossa"] = {
            "producer": "FOSSA",
            "status": "passed",
            "evidence": ["artifact: fossa.json"],
        }
        card = MODULE.scorecard(
            self.policy, self.evidence, "change", "abc123", catalog=self.catalog
        )
        self.assertEqual(card["status"], "GREEN")
        self.assertEqual(card["advisory"]["percent"], 100.0)
        self.assertEqual(card["readiness_status"], "GREEN")

    def test_advisory_failure_does_not_make_readiness_red(self) -> None:
        self.evidence["checks"]["fossa"] = {
            "producer": "FOSSA",
            "status": "failed",
            "evidence": ["artifact: fossa.json"],
        }
        card = MODULE.scorecard(
            self.policy, self.evidence, "change", "abc123", catalog=self.catalog
        )
        self.assertEqual(card["decision"], "allow")
        self.assertEqual(card["readiness_status"], "ORANGE")
        self.assertEqual(card["enforced_readiness_red"], 0)

    def test_all_catalog_controls_exposes_unconfigured_services(self) -> None:
        self.catalog["controls"].append(
            {"id": "sonarqube", "name": "SonarQube", "activation": "external"}
        )
        card = MODULE.scorecard(
            self.policy,
            self.evidence,
            "change",
            "abc123",
            catalog=self.catalog,
            all_catalog_controls=True,
        )
        self.assertEqual(card["readiness"]["ORANGE"], 1)
        self.assertEqual(card["readiness"]["GRAY"], 1)
        self.assertFalse(card["controls"][-1]["in_policy"])
        self.assertEqual(card["controls"][-1]["enforcement"], "not_activated")
        self.assertEqual(card["controls"][-1]["evidence_status"], "not_activated")
        self.assertEqual(card["controls"][-1]["enforcement"], "not_activated")
        self.assertEqual(card["controls"][-1]["evidence_status"], "not_activated")


if __name__ == "__main__":
    unittest.main()
