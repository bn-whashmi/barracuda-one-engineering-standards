from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "evaluate.py"
SPEC = importlib.util.spec_from_file_location("agent_safe_evaluate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def policy() -> dict:
    return {
        "version": 1,
        "name": "test",
        "operations": {
            "change": {
                "required": ["regression"],
                "advisory": ["sast"],
            }
        },
    }


def evidence(
    *,
    regression: str = "passed",
    sast: str = "passed",
    revision: str = "abc123",
) -> dict:
    records = {
        "regression": {
            "producer": "tests",
            "status": regression,
        },
        "sast": {
            "producer": "scanner",
            "status": sast,
        },
    }
    for record in records.values():
        if record["status"] in {"passed", "failed"}:
            record["evidence"] = ["artifact: result.json"]
        else:
            record["reason"] = "producer was unavailable"
    return {
        "version": 1,
        "subject": {"type": "git-commit", "revision": revision},
        "checks": records,
    }


class EvaluateTests(unittest.TestCase):
    def test_allows_when_required_checks_pass(self) -> None:
        result = MODULE.evaluate(policy(), evidence(), "change", "abc123")
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["summary"]["required"], {"passed": 1, "total": 1})

    def test_blocks_missing_required_evidence(self) -> None:
        document = evidence()
        del document["checks"]["regression"]
        result = MODULE.evaluate(policy(), document, "change", "abc123")
        self.assertEqual(result["decision"], "block")
        self.assertEqual(result["findings"][0]["status"], "missing")

    def test_non_passing_status_does_not_satisfy_required_check(self) -> None:
        for status in ("failed", "blocked", "not_run"):
            with self.subTest(status=status):
                result = MODULE.evaluate(
                    policy(), evidence(regression=status), "change", "abc123"
                )
                self.assertEqual(result["decision"], "block")

    def test_advisory_failure_does_not_block(self) -> None:
        result = MODULE.evaluate(
            policy(), evidence(sast="failed"), "change", "abc123"
        )
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["findings"][0]["enforcement"], "advisory")

    def test_revision_mismatch_blocks(self) -> None:
        result = MODULE.evaluate(policy(), evidence(), "change", "different")
        self.assertEqual(result["decision"], "block")
        self.assertEqual(result["findings"][0]["check"], "_revision")

    def test_rejects_passed_check_without_evidence_record(self) -> None:
        document = evidence()
        del document["checks"]["regression"]["evidence"]
        with self.assertRaisesRegex(ValueError, "must contain at least one"):
            MODULE.evaluate(policy(), document, "change", "abc123")

    def test_rejects_check_in_both_enforcement_levels(self) -> None:
        document = policy()
        document["operations"]["change"]["advisory"].append("regression")
        with self.assertRaisesRegex(ValueError, "both required and advisory"):
            MODULE.evaluate(document, evidence(), "change", "abc123")

    def test_rejects_unknown_operation(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not define operation"):
            MODULE.evaluate(policy(), evidence(), "release", "abc123")


if __name__ == "__main__":
    unittest.main()
