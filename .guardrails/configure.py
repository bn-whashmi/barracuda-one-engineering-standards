#!/usr/bin/env python3
"""Select guardrail controls and enforcement levels for a repository policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MODES = ("advisory", "enforced")
OPERATIONS = ("change", "release")


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON-compatible YAML {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def catalog_controls(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    controls = catalog.get("controls")
    if not isinstance(controls, list):
        raise ValueError("catalog must contain a controls list")
    result: dict[str, dict[str, Any]] = {}
    for control in controls:
        if not isinstance(control, dict) or not isinstance(control.get("id"), str):
            raise ValueError("every catalog control must have a string id")
        result[control["id"]] = control
    return result


def validate_policy(policy: dict[str, Any]) -> None:
    operations = policy.get("operations")
    if not isinstance(operations, dict) or not operations:
        raise ValueError("policy must contain at least one operation")
    for operation, rules in operations.items():
        if not isinstance(rules, dict):
            raise ValueError(f"policy operation {operation} must be an object")
        for key in ("required", "advisory"):
            if not isinstance(rules.get(key), list) or not all(
                isinstance(value, str) for value in rules[key]
            ):
                raise ValueError(f"policy operation {operation}.{key} must be a list of ids")
        overlap = set(rules["required"]) & set(rules["advisory"])
        if overlap:
            raise ValueError(
                f"policy operation {operation} lists controls in both modes: "
                + ", ".join(sorted(overlap))
            )


def set_mode(policy: dict[str, Any], control_id: str, mode: str, operations: list[str]) -> None:
    if mode not in MODES:
        raise ValueError(f"mode must be one of: {', '.join(MODES)}")
    for operation in operations:
        if operation not in policy["operations"]:
            raise ValueError(f"policy does not define operation: {operation}")
        rules = policy["operations"][operation]
        rules["required"] = [item for item in rules["required"] if item != control_id]
        rules["advisory"] = [item for item in rules["advisory"] if item != control_id]
        if mode == "enforced":
            rules["required"].append(control_id)
        elif mode == "advisory":
            rules["advisory"].append(control_id)


def current_mode(policy: dict[str, Any], control_id: str, operation: str) -> str:
    rules = policy["operations"].get(operation, {})
    if control_id in rules.get("required", []):
        return "enforced"
    if control_id in rules.get("advisory", []):
        return "advisory"
    return "not_activated"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure guardrail controls as advisory or enforced"
    )
    parser.add_argument("--policy", type=Path, default=Path(".ai/guardrails.yaml"))
    parser.add_argument("--catalog", type=Path, default=Path(".ai/control-catalog.yaml"))
    parser.add_argument("--operation", choices=OPERATIONS, default="change")
    parser.add_argument(
        "--all-operations",
        action="store_true",
        help="apply each --set choice to every operation in the policy",
    )
    parser.add_argument(
        "--set",
        action="append",
        metavar="CONTROL=MODE",
        help="set a control to advisory or enforced; repeatable",
    )
    parser.add_argument("--list", action="store_true", help="list catalog controls and current modes")
    parser.add_argument("--dry-run", action="store_true", help="show changes without writing the policy")
    args = parser.parse_args()

    try:
        policy = load_object(args.policy)
        catalog = catalog_controls(load_object(args.catalog))
        validate_policy(policy)
        operations = list(policy["operations"]) if args.all_operations else [args.operation]
        if args.list:
            for control_id, control in catalog.items():
                mode = current_mode(policy, control_id, args.operation)
                print(
                    f"{mode:9} {control_id:28} {control.get('name', control_id)} "
                    f"[{control.get('activation', 'unknown')}]"
                )
            return 0
        if not args.set:
            raise ValueError("provide --set CONTROL=MODE or use --list")
        for choice in args.set:
            if "=" not in choice:
                raise ValueError(f"invalid selection {choice!r}; expected CONTROL=MODE")
            control_id, mode = choice.split("=", 1)
            if control_id not in catalog:
                raise ValueError(f"unknown catalog control: {control_id}")
            set_mode(policy, control_id, mode, operations)
        validate_policy(policy)
        rendered = json.dumps(policy, indent=2) + "\n"
        if args.dry_run:
            print(rendered, end="")
        else:
            args.policy.write_text(rendered, encoding="utf-8")
            print(f"Updated {args.policy}")
            for choice in args.set:
                print(f"- {choice} for {', '.join(operations)}")
        return 0
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
