#!/usr/bin/env python3
"""Render a compliance scorecard from policy and revision-bound evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "guardrails" / "evaluate.py"
if not EVALUATOR_PATH.exists():
    EVALUATOR_PATH = ROOT / ".guardrails" / "evaluate.py"

PUBLIC_EVIDENCE_STATUS = {
    "passed": "passed",
    "failed": "failed",
    "blocked": "blocked",
    "not_run": "no_result",
    "missing": "not_activated",
}


def public_evidence_status(status: str) -> str:
    return PUBLIC_EVIDENCE_STATUS.get(status, status)


def public_finding_message(message: str) -> str:
    """Keep evaluator implementation terms out of the public scorecard."""
    return (
        message.replace("not_run", "no result")
        .replace("missing", "not activated")
        .replace("required", "enforced")
    )


def evaluator_module() -> Any:
    spec = importlib.util.spec_from_file_location("guardrails_evaluator", EVALUATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    if not spec or not spec.loader:
        raise ValueError(f"cannot load evaluator: {EVALUATOR_PATH}")
    spec.loader.exec_module(module)
    return module


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def percentage(passed: int, total: int) -> float | None:
    return round((passed / total) * 100, 1) if total else None


def activation_map(catalog: dict[str, Any]) -> dict[str, str]:
    return {
        control["id"]: control["activation"]
        for control in catalog.get("controls", [])
        if isinstance(control, dict)
        and isinstance(control.get("id"), str)
        and control.get("activation") in {"github-native", "external", "repository"}
    }


def readiness_rows(
    policy: dict[str, Any],
    evidence: dict[str, Any],
    operation: str,
    catalog: dict[str, Any] | None,
    *,
    all_catalog_controls: bool,
) -> list[dict[str, Any]]:
    definitions = {
        control["id"]: control
        for control in (catalog or {}).get("controls", [])
        if isinstance(control, dict) and isinstance(control.get("id"), str)
    }
    policy_controls = [
        *policy["operations"][operation]["required"],
        *policy["operations"][operation]["advisory"],
    ]
    control_ids = (
        list(definitions)
        if all_catalog_controls and definitions
        else policy_controls
    )
    required = set(policy["operations"][operation]["required"])
    advisory = set(policy["operations"][operation]["advisory"])
    evidence_checks = evidence.get("checks", {})
    rows = []
    for control_id in control_ids:
        definition = definitions.get(control_id, {})
        activation = definition.get("activation", "unknown")
        source_evidence_status = evidence_checks.get(control_id, {}).get("status", "missing")
        if source_evidence_status == "passed":
            readiness = "GREEN"
        elif source_evidence_status in {"failed", "blocked"}:
            readiness = "RED"
        elif control_id in required:
            readiness = "RED"
        elif control_id in advisory:
            readiness = "ORANGE"
        else:
            readiness = "GRAY"
        rows.append(
            {
                "id": control_id,
                "name": definition.get("name", control_id),
                "activation": activation,
                "readiness": readiness,
                "evidence_status": public_evidence_status(source_evidence_status),
                "enforcement": (
                    "enforced" if control_id in required
                    else "advisory" if control_id in advisory
                    else "not_activated"
                ),
                "in_policy": control_id in required or control_id in advisory,
            }
        )
    return rows


def scorecard(
    policy: dict[str, Any],
    evidence: dict[str, Any],
    operation: str,
    revision: str,
    *,
    subject_type: str | None = None,
    catalog: dict[str, Any] | None = None,
    all_catalog_controls: bool = False,
) -> dict[str, Any]:
    evaluator = evaluator_module()
    result = evaluator.evaluate(policy, evidence, operation, revision, subject_type)
    required = result["summary"]["required"]
    advisory = result["summary"]["advisory"]
    findings = [
        {
            **finding,
            "enforcement": "enforced" if finding["enforcement"] == "required" else "advisory",
            "status": public_evidence_status(finding["status"]),
            "message": public_finding_message(finding["message"]),
        }
        for finding in result["findings"]
    ]
    if result["decision"] == "block":
        status = "RED"
    elif findings:
        status = "ORANGE"
    else:
        status = "GREEN"

    activation = {"github-native": 0, "external": 0, "repository": 0, "unknown": 0}
    controls = [*policy["operations"][operation]["required"], *policy["operations"][operation]["advisory"]]
    known = activation_map(catalog or {})
    for control in controls:
        activation[known.get(control, "unknown")] += 1

    controls_readiness = readiness_rows(
        policy,
        evidence,
        operation,
        catalog,
        all_catalog_controls=all_catalog_controls,
    )
    readiness = {status: 0 for status in ("GREEN", "ORANGE", "GRAY", "RED")}
    for control in controls_readiness:
        readiness[control["readiness"]] += 1
    required_ids = set(policy["operations"][operation]["required"])
    required_red = sum(
        1 for control in controls_readiness
        if control["id"] in required_ids and control["readiness"] == "RED"
    )
    advisory_or_unselected_gap = any(
        control["readiness"] != "GREEN" for control in controls_readiness
        if control["id"] not in required_ids
    )
    readiness_status = (
        "RED" if required_red else
        "ORANGE" if advisory_or_unselected_gap else
        "GREEN"
    )

    return {
        "version": 1,
        "status": status,
        "decision": result["decision"],
        "policy": result["policy"],
        "operation": result["operation"],
        "subject": result["subject"],
        "enforced": {
            **required,
            "percent": percentage(required["passed"], required["total"]),
        },
        "advisory": {
            **advisory,
            "percent": percentage(advisory["passed"], advisory["total"]),
        },
        "activation": activation,
        "readiness_status": readiness_status,
        "readiness": readiness,
        "enforced_readiness_red": required_red,
        "controls": controls_readiness,
        "findings": findings,
    }


def render(card: dict[str, Any]) -> str:
    subject = card["subject"]
    lines = [
        f"Guardrail Scorecard: {card['status']}",
        f"Decision: {card['decision'].upper()}",
        f"Service readiness: {card['readiness_status']} (enforced RED: {card['enforced_readiness_red']})",
        f"Policy: {card['policy']} ({card['operation']})",
        f"Revision: {subject['revision']}",
        (
            f"Enforced compliance: {card['enforced']['passed']}/"
            f"{card['enforced']['total']} ({card['enforced']['percent'] or 0}%)"
        ),
        (
            f"Advisory coverage: {card['advisory']['passed']}/"
            f"{card['advisory']['total']} ({card['advisory']['percent'] or 0}%)"
        ),
        (
            "Activation: "
            f"GREEN {card['activation']['github-native']}, "
            f"ORANGE {card['activation']['external']}, "
            f"GRAY {card['activation']['repository']}, "
            f"UNKNOWN {card['activation']['unknown']}"
        ),
        (
            "Controls: "
            f"GREEN {card['readiness']['GREEN']}, "
            f"ORANGE {card['readiness']['ORANGE']}, "
            f"GRAY {card['readiness']['GRAY']}, "
            f"RED {card['readiness']['RED']}"
        ),
    ]
    for control in card["controls"]:
        lines.append(
            f"  {control['readiness']} {control['id']}: "
            f"{control['evidence_status']} ({control['activation']})"
        )
    for finding in card["findings"]:
        lines.append(
            f"- {finding['enforcement']} {finding['check']}: "
            f"{finding['status']} — {finding['message']}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a guardrail compliance scorecard")
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--subject-type")
    parser.add_argument("--catalog", type=Path)
    parser.add_argument(
        "--all-catalog-controls",
        action="store_true",
        help="include catalog controls not selected by the operation policy",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        catalog = load_json_object(args.catalog) if args.catalog else None
        card = scorecard(
            load_json_object(args.policy),
            load_json_object(args.evidence),
            args.operation,
            args.revision,
            subject_type=args.subject_type,
            catalog=catalog,
            all_catalog_controls=args.all_catalog_controls,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(card, indent=2) if args.json else render(card), end="")
    return 0 if card["decision"] == "allow" else 1


if __name__ == "__main__":
    raise SystemExit(main())
