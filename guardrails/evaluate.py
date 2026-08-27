#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
STATUSES = {"passed", "failed", "blocked", "not_run"}


def load_document(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{path} must use JSON-compatible YAML: {error}"
        ) from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def require_keys(
    value: dict[str, Any],
    *,
    required: set[str],
    allowed: set[str],
    label: str,
) -> None:
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - allowed)
    failures = [
        *[f"{label}.{key} is required" for key in missing],
        *[f"{label}.{key} is not supported" for key in unknown],
    ]
    if failures:
        raise ValueError("; ".join(failures))


def valid_identifier(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= 80
        and IDENTIFIER.fullmatch(value) is not None
    )


def validate_check_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    if not all(valid_identifier(item) for item in value):
        raise ValueError(f"{label} contains an invalid check identifier")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicate checks")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    require_keys(
        policy,
        required={"version", "name", "operations"},
        allowed={"$schema", "version", "name", "operations"},
        label="policy",
    )
    if policy["version"] != 1:
        raise ValueError("policy.version must be 1")
    if (
        not isinstance(policy["name"], str)
        or not policy["name"].strip()
        or len(policy["name"]) > 100
    ):
        raise ValueError("policy.name must be 1-100 characters")
    if "$schema" in policy and not isinstance(policy["$schema"], str):
        raise ValueError("policy.$schema must be a string")
    operations = policy["operations"]
    if not isinstance(operations, dict) or not operations:
        raise ValueError("policy.operations must be a non-empty object")
    for operation, rules in operations.items():
        if not valid_identifier(operation):
            raise ValueError(f"policy operation {operation!r} is invalid")
        if not isinstance(rules, dict):
            raise ValueError(f"policy.operations.{operation} must be an object")
        require_keys(
            rules,
            required={"required", "advisory"},
            allowed={"required", "advisory"},
            label=f"policy.operations.{operation}",
        )
        required = validate_check_list(
            rules["required"], f"policy.operations.{operation}.required"
        )
        advisory = validate_check_list(
            rules["advisory"], f"policy.operations.{operation}.advisory"
        )
        overlap = sorted(set(required) & set(advisory))
        if overlap:
            raise ValueError(
                f"policy operation {operation} lists checks as both required "
                f"and advisory: {', '.join(overlap)}"
            )


def validate_evidence(evidence: dict[str, Any]) -> None:
    require_keys(
        evidence,
        required={"version", "subject", "checks"},
        allowed={"$schema", "version", "subject", "checks"},
        label="evidence",
    )
    if evidence["version"] != 1:
        raise ValueError("evidence.version must be 1")
    if "$schema" in evidence and not isinstance(evidence["$schema"], str):
        raise ValueError("evidence.$schema must be a string")
    subject = evidence["subject"]
    if not isinstance(subject, dict):
        raise ValueError("evidence.subject must be an object")
    require_keys(
        subject,
        required={"type", "revision"},
        allowed={"type", "revision"},
        label="evidence.subject",
    )
    if not valid_identifier(subject["type"]):
        raise ValueError("evidence.subject.type is invalid")
    if (
        not isinstance(subject["revision"], str)
        or not subject["revision"]
        or len(subject["revision"]) > 200
    ):
        raise ValueError("evidence.subject.revision must be 1-200 characters")

    checks = evidence["checks"]
    if not isinstance(checks, dict):
        raise ValueError("evidence.checks must be an object")
    for name, check in checks.items():
        if not valid_identifier(name):
            raise ValueError(f"evidence check {name!r} is invalid")
        if not isinstance(check, dict):
            raise ValueError(f"evidence.checks.{name} must be an object")
        require_keys(
            check,
            required={"producer", "status"},
            allowed={"producer", "status", "evidence", "reason"},
            label=f"evidence.checks.{name}",
        )
        if (
            not isinstance(check["producer"], str)
            or not check["producer"].strip()
            or len(check["producer"]) > 200
        ):
            raise ValueError(
                f"evidence.checks.{name}.producer must be 1-200 characters"
            )
        status = check["status"]
        if status not in STATUSES:
            raise ValueError(
                f"evidence.checks.{name}.status must be one of "
                f"{', '.join(sorted(STATUSES))}"
            )
        if status in {"passed", "failed"}:
            records = check.get("evidence")
            if (
                not isinstance(records, list)
                or not records
                or not all(
                    isinstance(item, str) and item and len(item) <= 1000
                    for item in records
                )
            ):
                raise ValueError(
                    f"evidence.checks.{name}.evidence must contain at least "
                    f"one record when status is {status}"
                )
        if status in {"blocked", "not_run"} and (
            not isinstance(check.get("reason"), str)
            or not check["reason"].strip()
            or len(check["reason"]) > 1000
        ):
            raise ValueError(
                f"evidence.checks.{name}.reason is required when status is {status}"
            )


def evaluate(
    policy: dict[str, Any],
    evidence: dict[str, Any],
    operation: str,
    expected_revision: str,
    expected_subject_type: str | None = None,
) -> dict[str, Any]:
    validate_policy(policy)
    validate_evidence(evidence)
    if not expected_revision or len(expected_revision) > 200:
        raise ValueError("expected revision must be 1-200 characters")
    if expected_subject_type and not valid_identifier(expected_subject_type):
        raise ValueError("expected subject type is invalid")
    operations = policy["operations"]
    if operation not in operations:
        raise ValueError(f"policy does not define operation {operation!r}")

    subject = evidence["subject"]
    rules = operations[operation]
    checks = evidence["checks"]
    findings: list[dict[str, str]] = []

    if subject["revision"] != expected_revision:
        findings.append(
            {
                "check": "_revision",
                "enforcement": "required",
                "status": "mismatch",
                "message": "evidence revision does not match the evaluated revision",
            }
        )
    if expected_subject_type and subject["type"] != expected_subject_type:
        findings.append(
            {
                "check": "_subject_type",
                "enforcement": "required",
                "status": "mismatch",
                "message": "evidence subject type does not match the evaluated subject",
            }
        )

    counts: dict[str, dict[str, int]] = {}
    for enforcement in ("required", "advisory"):
        passed = 0
        for name in rules[enforcement]:
            status = checks.get(name, {}).get("status", "missing")
            if status == "passed":
                passed += 1
                continue
            findings.append(
                {
                    "check": name,
                    "enforcement": enforcement,
                    "status": status,
                    "message": (
                        f"{enforcement} check {name!r} is {status}; "
                        "only passed evidence satisfies a check"
                    ),
                }
            )
        counts[enforcement] = {
            "passed": passed,
            "total": len(rules[enforcement]),
        }

    blocked = any(
        finding["enforcement"] == "required" for finding in findings
    )
    return {
        "version": 1,
        "decision": "block" if blocked else "allow",
        "policy": policy["name"],
        "operation": operation,
        "subject": subject,
        "summary": counts,
        "findings": findings,
    }


def render(result: dict[str, Any]) -> str:
    subject = result["subject"]
    required = result["summary"]["required"]
    advisory = result["summary"]["advisory"]
    lines = [
        f"{result['decision'].upper()} {result['operation']} "
        f"{subject['type']}@{subject['revision']}",
        f"Required: {required['passed']}/{required['total']} passed",
        f"Advisory: {advisory['passed']}/{advisory['total']} passed",
    ]
    for finding in result["findings"]:
        lines.append(
            f"- {finding['enforcement']} {finding['check']}: "
            f"{finding['status']}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate revision-bound evidence against a guardrail policy"
    )
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--subject-type")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = evaluate(
            load_document(args.policy),
            load_document(args.evidence),
            args.operation,
            args.revision,
            args.subject_type,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    output = json.dumps(result, indent=2) + "\n" if args.json else render(result)
    print(output, end="")
    return 0 if result["decision"] == "allow" else 1


if __name__ == "__main__":
    raise SystemExit(main())
