from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[3]
RUNNER = SKILLS_ROOT / "full-test-suite" / "scripts" / "full_test_suite_runner.py"
EXECUTOR = SKILLS_ROOT / "full-test-suite" / "scripts" / "full_test_suite_executor.py"
STATE_SCRIPT = SKILLS_ROOT / "_shared-project-ops" / "scripts" / "project_ops_state.py"


class FullTestSuiteExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        subprocess.run(["git", "-C", str(self.root), "init"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "checkout", "-b", "codex/executor-test"], check=True, capture_output=True)
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
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.fake_state = self.root / "fake-codex-state.json"
        self.fake_state.write_text(json.dumps({"bug_created": False, "bug_fixed": False, "prompts": []}), encoding="utf-8")
        self._write_fake_codex()

        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.bin_dir}:{self.env['PATH']}"
        self.env["FAKE_CODEX_STATE"] = str(self.fake_state)

        subprocess.run(
            [
                "python3",
                str(RUNNER),
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
            ],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_fake_codex(self) -> None:
        script = self.bin_dir / "codex"
        script.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json
                import os
                import re
                import subprocess
                import sys
                from pathlib import Path

                state_path = Path(os.environ["FAKE_CODEX_STATE"])
                state = json.loads(state_path.read_text())
                args = sys.argv[1:]
                if not args or args[0] != "exec":
                    raise SystemExit(1)

                output_path = Path(args[args.index("-o") + 1])
                prompt = args[-1]
                state["prompts"].append(prompt)

                if os.environ.get("FAKE_CODEX_SLEEP"):
                    import time
                    time.sleep(float(os.environ["FAKE_CODEX_SLEEP"]))

                def line(prefix):
                    for value in prompt.splitlines():
                        if value.startswith(prefix):
                            return value[len(prefix):].strip()
                    return ""

                findings_path = line("FindingsPath:")
                manifest_path = line("ManifestPath:")
                skill = line("Skill:")
                finding_id = line("FindingId:")

                if "Action: run-skill" in prompt:
                    if skill == "bug-hunter" and not state["bug_created"]:
                        subprocess.run(
                            [
                                "python3",
                                "{STATE_SCRIPT}",
                                "upsert-finding",
                                "--path",
                                findings_path,
                                "--payload",
                                json.dumps({{"id": "BUG-001", "title": "Executor-created bug", "type": "bug", "severity": "high"}}),
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        state["bug_created"] = True
                    output = {{"status": "completed", "note": f"completed {{skill}}"}}
                elif "Action: fix-finding" in prompt:
                    subprocess.run(
                        [
                            "python3",
                            "{STATE_SCRIPT}",
                            "upsert-finding",
                            "--path",
                            findings_path,
                            "--payload",
                            json.dumps({{
                                "id": finding_id,
                                "status": "resolved",
                                "verification": ["executor regression test passed"],
                                "resolution_notes": ["Executor applied a deterministic fix."],
                            }}),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    state["bug_fixed"] = True
                    output = {{
                        "status": "resolved",
                        "fix_applied": True,
                        "note": "fixed the finding",
                        "verification": ["executor regression test passed"],
                        "surfaces_changed": ["App/Services/ExampleBackendClient.swift"],
                        "finding_types": ["bug"],
                    }}
                else:
                    output = {{"status": "completed", "note": "no-op"}}

                state_path.write_text(json.dumps(state))
                output_path.write_text(json.dumps(output))
                raise SystemExit(0)
                """
            ),
            encoding="utf-8",
        )
        script.chmod(0o755)

    def _executor(self, *args: str) -> dict:
        result = subprocess.run(
            ["python3", str(EXECUTOR), *args],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )
        return json.loads(result.stdout)

    def _executor_raw(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(EXECUTOR), *args],
            check=True,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def test_step_executes_skill_and_records_progress(self) -> None:
        payload = self._executor("step", "--manifest-path", str(self.manifest_path), "--codex-binary", "codex")
        self.assertEqual(payload["action"]["action"], "run-skill")
        self.assertEqual(payload["action"]["skill"], "project-health-check")

        report_text = self.report_path.read_text(encoding="utf-8")
        self.assertIn("- project-health-check: completed", report_text)

    def test_loop_runs_to_completion_with_fake_codex(self) -> None:
        payload = self._executor(
            "loop",
            "--manifest-path",
            str(self.manifest_path),
            "--codex-binary",
            "codex",
            "--max-steps",
            "20",
        )
        self.assertEqual(payload["status"], "completed")

        report_text = self.report_path.read_text(encoding="utf-8")
        findings_text = self.findings_path.read_text(encoding="utf-8")
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        self.assertIn("- Final state: no confirmed-open findings", report_text)
        self.assertIn("- Status: resolved", findings_text)
        self.assertEqual(manifest["status"], "completed")

    def test_run_bootstraps_and_completes_when_reinitialized(self) -> None:
        payload = self._executor(
            "run",
            "--repo-root",
            str(self.root),
            "--codex-binary",
            "codex",
            "--max-steps",
            "20",
            "--reinit",
        )
        self.assertEqual(payload["status"], "completed")
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "completed")

    def test_loop_prints_compact_step_summaries_to_stderr(self) -> None:
        result = self._executor_raw(
            "loop",
            "--manifest-path",
            str(self.manifest_path),
            "--codex-binary",
            "codex",
            "--max-steps",
            "20",
        )
        self.assertIn("[full-test-suite] step summary", result.stderr)
        self.assertIn("step: 1", result.stderr)
        self.assertIn("findings: open=", result.stderr)
        self.assertIn("next:", result.stderr)

    def test_run_reinit_archives_existing_artifacts(self) -> None:
        self.findings_path.write_text("# stale findings\n", encoding="utf-8")
        self.report_path.write_text("# stale report\n", encoding="utf-8")
        self.manifest_path.write_text('{"status":"stale"}\n', encoding="utf-8")

        payload = self._executor(
            "run",
            "--repo-root",
            str(self.root),
            "--codex-binary",
            "codex",
            "--max-steps",
            "20",
            "--reinit",
        )

        self.assertEqual(payload["status"], "completed")
        archived = sorted(self.root.glob("*.bak-*"))
        self.assertTrue(any(path.name.startswith("project-audit-findings.md.bak-") for path in archived))
        self.assertTrue(any(path.name.startswith("full-test-suite-report.md.bak-") for path in archived))
        self.assertTrue(any(path.name.startswith("full-test-suite-manifest.json.bak-") for path in archived))

    def test_loop_returns_blocked_when_codex_step_times_out(self) -> None:
        env = self.env.copy()
        env["FAKE_CODEX_SLEEP"] = "2"
        result = subprocess.run(
            [
                "python3",
                str(EXECUTOR),
                "loop",
                "--manifest-path",
                str(self.manifest_path),
                "--codex-binary",
                "codex",
                "--max-steps",
                "1",
                "--step-timeout-seconds",
                "1",
                "--heartbeat-seconds",
                "1",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("timed out", payload["error"])


if __name__ == "__main__":
    unittest.main()
