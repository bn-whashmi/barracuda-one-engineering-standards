from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ActionDistributionTests(unittest.TestCase):
    def test_repository_runtime_collector_matches_distribution_source(self) -> None:
        self.assertEqual(
            (ROOT / ".guardrails" / "github_evidence.py").read_text(encoding="utf-8"),
            (ROOT / "tooling" / "github_evidence.py").read_text(encoding="utf-8"),
        )

    def test_action_is_a_thin_evaluator_adapter(self) -> None:
        text = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertIn("branding:", text)
        self.assertIn("icon: shield", text)
        self.assertIn("title=Missing revision", text)
        self.assertIn("title=Missing evidence", text)
        self.assertIn("title=Missing policy", text)
        self.assertIn("guardrails/evaluate.py", text)
        self.assertNotIn("git diff", text)

    def test_starter_workflow_uses_least_privilege_and_pinned_actions(self) -> None:
        text = (
            ROOT
            / "docs"
            / "examples"
            / "guardrails.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)
        action_refs = re.findall(r"uses:\s+[^@\s]+@([^\s]+)", text)
        self.assertTrue(action_refs)
        self.assertTrue(
            all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_refs)
        )
        self.assertIn("checks: read", text)
        self.assertIn(".guardrails/github_evidence.py", text)
        self.assertIn(".guardrails/producer-manifest.json", text)
        self.assertIn(".guardrails/scan.py", text)
        workflow = (ROOT / "docs" / "examples" / "guardrails.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("publish-scorecard:", workflow)
        self.assertIn("actions/download-artifact@", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("<!-- guardrail-scorecard -->", workflow)
        self.assertIn("<!-- agentic-guardrail-scorecard -->", workflow)
        self.assertNotIn("pull-requests: write\n\nconcurrency:", workflow)
        publisher = workflow.split("  publish-scorecard:", 1)[1]
        self.assertNotIn("actions/checkout@", publisher)

    def test_repository_workflow_checks_ground_truth_docs_and_scope_on_every_push(self) -> None:
        text = (
            ROOT / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("  docs:\n", text)
        self.assertIn("  scope:\n", text)
        self.assertIn("  ground-truth:\n", text)
        self.assertIn("name: Validate / docs", text)
        self.assertIn("name: Validate / scope", text)
        self.assertIn("name: Validate / ground truth", text)
        self.assertIn("name: Validate / repository", text)
        self.assertIn("needs: [docs, scope, ground-truth]", text)
        self.assertIn(".guardrails/validate_ground_truth.py", text)
        self.assertIn("tooling/validators/validate_documentation.py", text)
        self.assertIn("tooling/validators/inspect_change_scope.py", text)
        self.assertIn("PUSH_FORCED: ${{ github.event.forced || false }}", text)
        self.assertIn('[[ "$PUSH_FORCED" != "true"', text)
        self.assertNotIn("branches: [main]", text)

    def test_secret_scan_workflow_verifies_github_platform_settings(self) -> None:
        text = (ROOT / ".github" / "workflows" / "secret-scan.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Secret Scanning and push protection", text)
        self.assertIn("security_and_analysis.secret_scanning.status", text)
        self.assertIn("security_and_analysis.secret_scanning_push_protection.status", text)
        self.assertIn("secret-scanning/alerts", text)
        self.assertIn("head_sha", text)
        self.assertIn("checks: write", text)
        self.assertIn("no-checkout verifier", text)
        self.assertNotIn("actions/checkout@", text)
        org = (ROOT / ".github" / "workflows" / "organization-secret-scan.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Secret Scan / organization scanner", org)
        self.assertIn("pull_request:", org)
        self.assertNotIn("SECURITY_SETTINGS_TOKEN", org)

    def test_codeql_workflow_publishes_the_manifest_check_name(self) -> None:
        text = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: CodeQL", text)
        self.assertIn("github/codeql-action/init@", text)
        self.assertIn("github/codeql-action/analyze@", text)
        self.assertIn("security-events: write", text)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", text)

    def test_default_ruleset_does_not_define_an_empty_required_check_rule(self) -> None:
        ruleset = json.loads(
            (ROOT / "rulesets" / "default-branch-protection.json").read_text(
                encoding="utf-8"
            )
        )
        required_check_rules = [
            rule for rule in ruleset["rules"] if rule["type"] == "required_status_checks"
        ]
        self.assertEqual([], required_check_rules)


if __name__ == "__main__":
    unittest.main()
