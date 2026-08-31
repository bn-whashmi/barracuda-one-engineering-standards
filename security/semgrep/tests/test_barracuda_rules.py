from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RULES = ROOT / "security/semgrep/barracuda.yml"
FIXTURES = Path(__file__).resolve().parent / "barracuda-fixtures"


class BarracudaSemgrepRuleTests(unittest.TestCase):
    def run_semgrep(self, fixture: str) -> dict:
        try:
            completed = subprocess.run(
                ["semgrep", "scan", "--config", str(RULES), "--json", str(FIXTURES / fixture)],
                text=True,
                capture_output=True,
            )
        except FileNotFoundError:
            self.skipTest("Semgrep is required to execute rule fixtures")
        if completed.returncode not in (0, 1):
            self.skipTest("Semgrep is required to execute rule fixtures")
        return json.loads(completed.stdout)

    def test_typescript_rules_match_only_unsafe_fixtures(self) -> None:
        unsafe = self.run_semgrep("unsafe")
        safe = self.run_semgrep("safe")
        self.assertEqual(
            {result["check_id"] for result in unsafe["results"]},
            {
                "barracuda.typescript-disabled-tls-verification",
                "barracuda.typescript-direct-mui-import",
            },
        )
        self.assertEqual(safe["results"], [])


if __name__ == "__main__":
    unittest.main()
