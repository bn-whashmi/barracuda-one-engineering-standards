from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("agent_safe_install", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class InstallerTests(unittest.TestCase):
    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plan = MODULE.install(target, dry_run=True)
            self.assertEqual(len(plan), 11)
            self.assertFalse((target / ".ai").exists())
            self.assertFalse((target / ".guardrails").exists())
            self.assertFalse((target / ".agents").exists())

    def test_installs_small_core(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            MODULE.install(target, dry_run=False)
            self.assertTrue((target / ".ai" / "guardrails.yaml").exists())
            self.assertTrue((target / ".ai" / "control-catalog.yaml").exists())
            self.assertTrue((target / ".guardrails" / "evaluate.py").exists())
            self.assertTrue((target / ".guardrails" / "scorecard.py").exists())
            self.assertTrue((target / ".guardrails" / "configure.py").exists())
            self.assertTrue((target / ".guardrails" / "scan.py").exists())
            self.assertTrue((target / ".guardrails" / "github_evidence.py").exists())
            self.assertTrue((target / ".guardrails" / "producer-manifest.json").exists())
            self.assertTrue((target / ".guardrails" / "providers.yaml").exists())
            self.assertTrue(
                (
                    target
                    / ".agents"
                    / "skills"
                    / "prepare-safe-change"
                    / "SKILL.md"
                ).exists()
            )

    def test_refuses_to_overwrite_existing_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            policy = target / ".ai" / "guardrails.yaml"
            policy.parent.mkdir(parents=True)
            policy.write_text("existing\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                MODULE.install(target, dry_run=False)

    def test_merge_existing_preserves_policy_and_installs_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            policy = target / ".ai" / "guardrails.yaml"
            policy.parent.mkdir(parents=True)
            policy.write_text("existing\n", encoding="utf-8")
            plan = MODULE.install(target, dry_run=False, merge_existing=True)
            self.assertFalse(any(item.destination == policy for item in plan))
            self.assertEqual(policy.read_text(encoding="utf-8"), "existing\n")
            self.assertTrue((target / ".guardrails" / "scan.py").exists())

    def test_refresh_existing_updates_product_without_overwriting_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            MODULE.install(target, dry_run=False)
            policy = target / ".ai" / "guardrails.yaml"
            policy.write_text("custom-policy\n", encoding="utf-8")
            scan = target / ".guardrails" / "scan.py"
            scan.write_text("stale\n", encoding="utf-8")
            MODULE.install(target, dry_run=False, refresh_existing=True)
            self.assertEqual(policy.read_text(encoding="utf-8"), "custom-policy\n")
            self.assertNotEqual(scan.read_text(encoding="utf-8"), "stale\n")
            self.assertTrue((target / ".guardrails" / "providers.yaml").exists())

    def test_refresh_existing_removes_only_known_legacy_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            legacy = target / ".ai" / "providers.yaml"
            legacy_manifest = target / ".ai" / "producer-manifest.json"
            other = target / ".ai" / "application-config.yaml"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("legacy\n", encoding="utf-8")
            legacy_manifest.write_text("legacy manifest\n", encoding="utf-8")
            other.write_text("keep\n", encoding="utf-8")

            plan = MODULE.install(target, dry_run=False, refresh_existing=True)

            self.assertFalse(legacy.exists())
            self.assertFalse(legacy_manifest.exists())
            self.assertEqual(other.read_text(encoding="utf-8"), "keep\n")
            self.assertTrue(
                any(item.kind == "remove" and item.destination == legacy.resolve() for item in plan)
            )
            self.assertTrue(
                any(item.kind == "remove" and item.destination == legacy_manifest.resolve() for item in plan)
            )

    def test_refresh_existing_migrates_agentic_guardrails_configuration_and_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            legacy_runtime = target / ".agentic-guardrails"
            legacy_runtime.mkdir(parents=True)
            (legacy_runtime / "providers.yaml").write_text("custom providers\n", encoding="utf-8")
            (legacy_runtime / "producer-manifest.json").write_text(
                '{"custom": true}\n', encoding="utf-8"
            )
            (legacy_runtime / "scan.py").write_text("stale runtime\n", encoding="utf-8")
            (legacy_runtime / "consumer-notes.md").write_text("keep me\n", encoding="utf-8")
            legacy_workflow = (
                target / ".github" / "workflows" / "agentic-guardrails-scorecard.yml"
            )
            legacy_workflow.parent.mkdir(parents=True)
            legacy_workflow.write_text(
                "name: Agentic Guardrail Scorecard\nrun: python3 .agentic-guardrails/scan.py\n",
                encoding="utf-8",
            )

            MODULE.install(
                target,
                dry_run=False,
                github_actions=True,
                refresh_existing=True,
            )

            self.assertEqual(
                (target / ".guardrails" / "providers.yaml").read_text(encoding="utf-8"),
                "custom providers\n",
            )
            self.assertEqual(
                (target / ".guardrails" / "producer-manifest.json").read_text(encoding="utf-8"),
                '{"custom": true}\n',
            )
            migrated_workflow = target / ".github" / "workflows" / "guardrails-scorecard.yml"
            self.assertIn("name: Guardrail Scorecard", migrated_workflow.read_text(encoding="utf-8"))
            self.assertIn(".guardrails/scan.py", migrated_workflow.read_text(encoding="utf-8"))
            self.assertFalse((legacy_runtime / "providers.yaml").exists())
            self.assertFalse((legacy_runtime / "producer-manifest.json").exists())
            self.assertFalse((legacy_runtime / "scan.py").exists())
            self.assertFalse(legacy_workflow.exists())
            self.assertEqual(
                (legacy_runtime / "consumer-notes.md").read_text(encoding="utf-8"),
                "keep me\n",
            )

    def test_refresh_existing_preserves_consumer_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            manifest = target / ".guardrails" / "producer-manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("consumer manifest\n", encoding="utf-8")

            MODULE.install(target, dry_run=False, refresh_existing=True)

            self.assertEqual(manifest.read_text(encoding="utf-8"), "consumer manifest\n")

    def test_refresh_dry_run_reports_cleanup_without_removing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            legacy = target / ".ai" / "providers.yaml"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("legacy\n", encoding="utf-8")

            plan = MODULE.install(target, dry_run=True, refresh_existing=True)

            self.assertTrue(legacy.exists())
            self.assertTrue(any(item.kind == "remove" for item in plan))

    def test_cleanup_refuses_unexpected_legacy_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / ".ai" / "providers.yaml").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "directory"):
                MODULE.install(target, dry_run=False, refresh_existing=True)

    def test_refresh_existing_preserves_consumer_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            workflow = target / ".github" / "workflows" / "guardrails-attestation.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("consumer-owned\n", encoding="utf-8")

            MODULE.install(target, dry_run=False, github_actions=True, refresh_existing=True)

            self.assertEqual(workflow.read_text(encoding="utf-8"), "consumer-owned\n")
            self.assertTrue(
                (target / ".github" / "workflows" / "guardrails-scorecard.yml").exists()
            )

            scorecard = target / ".github" / "workflows" / "guardrails-scorecard.yml"
            scorecard.write_text("custom-scorecard\n", encoding="utf-8")
            MODULE.install(target, dry_run=False, github_actions=True, refresh_existing=True)
            self.assertEqual(scorecard.read_text(encoding="utf-8"), "custom-scorecard\n")

    def test_refresh_existing_preserves_provider_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            workflow = target / ".github" / "workflows" / "semgrep.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("consumer-customized\n", encoding="utf-8")

            MODULE.install(target, dry_run=False, providers=["semgrep"], refresh_existing=True)

            self.assertEqual(workflow.read_text(encoding="utf-8"), "consumer-customized\n")

    def test_installs_optional_github_actions_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plan = MODULE.install(
                target,
                dry_run=False,
                github_actions=True,
            )
            workflow = target / ".github" / "workflows" / "guardrails-scorecard.yml"
            self.assertEqual(len(plan), 12)
            self.assertTrue(workflow.exists())
            text = workflow.read_text(encoding="utf-8")
            self.assertIn("permissions:\n  contents: read", text)
            self.assertIn("persist-credentials: false", text)
            self.assertIn(".guardrails/github_evidence.py", text)
            self.assertIn(".guardrails/producer-manifest.json", text)
            self.assertIn(".guardrails/scan.py", text)
            self.assertIn("checks: read", text)

    def test_installs_verified_provider_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plan = MODULE.install(target, dry_run=False, providers=["semgrep"])
            self.assertEqual(len(plan), 12)
            self.assertTrue((target / ".github" / "workflows" / "semgrep.yml").exists())


if __name__ == "__main__":
    unittest.main()
