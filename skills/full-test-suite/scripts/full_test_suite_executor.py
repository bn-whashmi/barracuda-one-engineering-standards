#!/usr/bin/env python3
"""Execute manifest-driven full-test-suite actions through Codex CLI."""

from __future__ import annotations

import argparse
import json
import os
import select
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

SKILLS_ROOT = Path(__file__).resolve().parents[2]

from full_test_suite_runner import (  # noqa: E402
    finalize_run,
    init_run,
    load_findings,
    load_manifest,
    next_action,
    record_fix,
    record_skill,
    record_verification,
    run_issue_sync,
)


SKILL_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["completed", "blocked", "skipped"],
        },
        "note": {"type": "string"},
    },
    "required": ["status", "note"],
}

FIX_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["resolved", "blocked", "needs-context", "confirmed-open"],
        },
        "fix_applied": {"type": "boolean"},
        "note": {"type": "string"},
        "verification": {
            "type": "array",
            "items": {"type": "string"},
        },
        "surfaces_changed": {
            "type": "array",
            "items": {"type": "string"},
        },
        "finding_types": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["status", "fix_applied", "note", "verification", "surfaces_changed", "finding_types"],
}


def emit_progress(enabled: bool, message: str) -> None:
    if not enabled:
        return
    print(message, file=sys.stderr, flush=True)


def format_seconds(elapsed: float) -> str:
    if elapsed < 1:
        return f"{elapsed:.2f}s"
    if elapsed < 60:
        return f"{elapsed:.1f}s"
    minutes = int(elapsed // 60)
    seconds = int(round(elapsed % 60))
    return f"{minutes}m{seconds:02d}s"


def summarize_step(
    manifest_path: Path,
    step_index: int,
    step_result: dict[str, Any],
    elapsed_seconds: float,
) -> str:
    manifest = load_manifest(manifest_path)
    findings = load_findings(Path(manifest["findings_path"]))
    counts = findings.counts()
    action = step_result["action"]
    executor_result = step_result.get("executor_result", {})
    next_step = next_action(manifest_path)

    target = action["action"]
    if action["action"] == "run-skill":
        target = action["skill"]
    elif action["action"] == "fix-finding":
        target = action["finding"]["id"]

    result_status = (
        executor_result.get("status")
        or step_result.get("runner_result", {}).get("final_state")
        or "completed"
    )

    lines = [
        "[full-test-suite] step summary",
        f"  step: {step_index}",
        f"  action: {action['action']}",
        f"  target: {target}",
        f"  result: {result_status}",
        f"  elapsed: {format_seconds(elapsed_seconds)}",
        f"  next: {next_step.get('action')}",
        "  findings:"
        f" open={counts.get('confirmed-open', 0)}"
        f" in_progress={counts.get('in-progress', 0)}"
        f" resolved={counts.get('resolved', 0)}"
        f" blocked={counts.get('blocked', 0)}"
        f" needs_context={counts.get('needs-context', 0)}",
    ]

    if next_step.get("action") == "run-skill":
        lines.append(
            f"  next_target: {next_step.get('skill')} "
            f"(cycle {next_step.get('cycle')} {next_step.get('cycle_kind')})"
        )
    elif next_step.get("action") == "fix-finding":
        finding = next_step.get("finding", {})
        lines.append(f"  next_target: {finding.get('id')} [{finding.get('severity')}/{finding.get('type')}]")
    elif next_step.get("action") == "sync-issues":
        lines.append(f"  next_target: github-sync ({next_step.get('github_issue_sync', 'unknown')})")
    elif next_step.get("action") == "finalize":
        lines.append("  next_target: finalize run")

    return "\n".join(lines)


def codex_exec(
    codex_binary: str,
    repo_root: Path,
    prompt: str,
    schema: dict[str, Any],
    model: str | None,
    config_profile: str | None,
    danger_full_access: bool,
    progress: bool,
    step_timeout_seconds: int | None,
    heartbeat_seconds: int,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        schema_path = temp_root / "schema.json"
        output_path = temp_root / "result.json"
        schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

        command = [
            codex_binary,
            "exec",
            "-C",
            str(repo_root),
            "--add-dir",
            str(SKILLS_ROOT),
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
            "--color",
            "never",
        ]
        if config_profile:
            command.extend(["-p", config_profile])
        if model:
            command.extend(["-m", model])
        if danger_full_access:
            command.append("--dangerously-bypass-approvals-and-sandbox")
        else:
            command.append("--full-auto")
        command.append(prompt)

        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        emit_progress(progress, f"[full-test-suite] exec: {shlex.join(command)}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            bufsize=1,
        )
        output_lines: list[str] = []
        assert process.stdout is not None
        started_at = time.monotonic()
        last_output_at = started_at
        last_heartbeat_at = started_at
        while True:
            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            now = time.monotonic()
            if ready:
                line = process.stdout.readline()
                if line == "":
                    if process.poll() is not None:
                        break
                else:
                    output_lines.append(line)
                    last_output_at = now
                    if progress:
                        print(f"[codex] {line.rstrip()}", file=sys.stderr, flush=True)
            elif process.poll() is not None:
                break

            if progress and heartbeat_seconds > 0 and now - last_heartbeat_at >= heartbeat_seconds:
                emit_progress(
                    progress,
                    "[full-test-suite] waiting on codex exec "
                    f"(elapsed={format_seconds(now - started_at)}, idle={format_seconds(now - last_output_at)})",
                )
                last_heartbeat_at = now

            if step_timeout_seconds and now - started_at >= step_timeout_seconds:
                process.kill()
                process.wait()
                tail = "".join(output_lines[-20:]).strip()
                detail = f"codex exec timed out after {step_timeout_seconds}s"
                if tail:
                    detail = f"{detail}. Last output:\n{tail}"
                raise RuntimeError(detail)
        return_code = process.wait()
        combined_output = "".join(output_lines).strip()
        if return_code != 0:
            raise RuntimeError(combined_output or "codex exec failed")
        if not output_path.exists():
            raise RuntimeError("codex exec did not write the expected structured output file")
        return json.loads(output_path.read_text(encoding="utf-8"))


def build_skill_prompt(manifest: dict[str, Any], action: dict[str, Any], manifest_path: Path) -> str:
    skill = action["skill"]
    skill_path = SKILLS_ROOT / skill / "SKILL.md"
    lines = [
        "You are executing one deterministic full-test-suite action.",
        "Action: run-skill",
        f"Skill: {skill}",
        f"SkillPath: {skill_path}",
        f"RepoRoot: {manifest['repo_root']}",
        f"FindingsPath: {manifest['findings_path']}",
        f"ReportPath: {manifest['report_path']}",
        f"ManifestPath: {manifest_path}",
        f"CycleId: {action.get('cycle')}",
        f"CycleKind: {action.get('cycle_kind')}",
        "",
        f"Use [${skill}]({skill_path}) for this pass.",
        "Review the repository surface relevant to the skill, promote only evidence-backed findings, and update project-audit-findings.md.",
        "Use the shared project-ops state scripts when deterministic edits help.",
        "If you make code, docs, or test changes, verify them and write the evidence into the finding entry or related report notes.",
    ]
    if skill == "issue-operator":
        lines.extend(
            [
                "Important: do not run `gh_issue_helper.py sync`, `gh`, or any other networked GitHub operation from this nested skill pass.",
                "Inside full-test-suite, this skill should reconcile local findings/report state only and leave actual GitHub issue sync to the outer deterministic `sync-issues` action.",
                "If you need to mention GitHub state, note that deterministic sync will happen outside this nested pass.",
            ]
        )
    lines.extend(
        [
            "Do not finalize the suite and do not edit the manifest directly.",
            "Return only the structured JSON result required by the schema.",
        ]
    )
    return "\n".join(lines)


def build_fix_prompt(manifest: dict[str, Any], action: dict[str, Any], manifest_path: Path) -> str:
    finding = action["finding"]
    return "\n".join(
        [
            "You are executing one deterministic full-test-suite action.",
            "Action: fix-finding",
            f"FindingId: {finding['id']}",
            f"RepoRoot: {manifest['repo_root']}",
            f"FindingsPath: {manifest['findings_path']}",
            f"ReportPath: {manifest['report_path']}",
            f"ManifestPath: {manifest_path}",
            "",
            "Target finding JSON:",
            json.dumps(finding, indent=2, sort_keys=True),
            "",
            "Goal:",
            "- inspect the repo and the finding evidence before editing",
            "- if the finding is real and safely fixable, implement the smallest safe fix, verify it, and update the finding entry to resolved with verification and resolution notes",
            "- if it cannot be safely resolved in this run, update the finding entry to blocked or needs-context with concrete evidence",
            "- do not leave the finding unchanged at the end of the pass",
            "- do not finalize the suite and do not edit the manifest directly",
            "",
            "Return only the structured JSON result required by the schema.",
        ]
    )


def execute_step(
    manifest_path: Path,
    codex_binary: str = "codex",
    model: str | None = None,
    config_profile: str | None = None,
    danger_full_access: bool = False,
    progress: bool = True,
    step_timeout_seconds: int | None = None,
    heartbeat_seconds: int = 30,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    action = next_action(manifest_path)
    emit_progress(progress, f"[full-test-suite] next action: {json.dumps(action, sort_keys=True)}")

    if action["action"] == "run-skill":
        emit_progress(
            progress,
            f"[full-test-suite] running skill {action['skill']} in cycle {action.get('cycle')} ({action.get('cycle_kind')})",
        )
        result = codex_exec(
            codex_binary=codex_binary,
            repo_root=Path(manifest["repo_root"]),
            prompt=build_skill_prompt(manifest, action, manifest_path),
            schema=SKILL_RESULT_SCHEMA,
            model=model,
            config_profile=config_profile,
            danger_full_access=danger_full_access,
            progress=progress,
            step_timeout_seconds=step_timeout_seconds,
            heartbeat_seconds=heartbeat_seconds,
        )
        payload = record_skill(
            Path(manifest["report_path"]),
            action["skill"],
            result["status"],
            result["note"],
            manifest_path=manifest_path,
        )
        return {
            "action": action,
            "executor_result": result,
            "runner_result": payload,
        }

    if action["action"] == "fix-finding":
        emit_progress(
            progress,
            f"[full-test-suite] fixing {action['finding']['id']} ({action['finding']['severity']}/{action['finding']['type']})",
        )
        result = codex_exec(
            codex_binary=codex_binary,
            repo_root=Path(manifest["repo_root"]),
            prompt=build_fix_prompt(manifest, action, manifest_path),
            schema=FIX_RESULT_SCHEMA,
            model=model,
            config_profile=config_profile,
            danger_full_access=danger_full_access,
            progress=progress,
            step_timeout_seconds=step_timeout_seconds,
            heartbeat_seconds=heartbeat_seconds,
        )
        for item in result.get("verification", []):
            record_verification(Path(manifest["report_path"]), item)
        runner_result: dict[str, Any]
        if result.get("fix_applied"):
            runner_result = record_fix(
                manifest_path=manifest_path,
                finding_id=action["finding"]["id"],
                surfaces=result.get("surfaces_changed", []),
                finding_types=result.get("finding_types", []),
                note=result.get("note"),
            )
        else:
            runner_result = {
                "manifest_path": str(manifest_path),
                "next_action": next_action(manifest_path),
            }
        return {
            "action": action,
            "executor_result": result,
            "runner_result": runner_result,
        }

    if action["action"] == "sync-issues":
        emit_progress(progress, "[full-test-suite] syncing GitHub issues")
        result = run_issue_sync(manifest_path)
        return {
            "action": action,
            "runner_result": result,
        }

    if action["action"] == "finalize":
        emit_progress(progress, "[full-test-suite] finalizing run")
        result = finalize_run(
            repo_root=Path(manifest["repo_root"]),
            findings_path=Path(manifest["findings_path"]),
            report_path=Path(manifest["report_path"]),
            manifest_path=manifest_path,
        )
        return {
            "action": action,
            "runner_result": result,
        }

    return {"action": action, "runner_result": {"reason": action.get("reason", "No action executed.")}}


def execute_loop(
    manifest_path: Path,
    codex_binary: str = "codex",
    model: str | None = None,
    config_profile: str | None = None,
    danger_full_access: bool = False,
    max_steps: int = 50,
    progress: bool = True,
    step_timeout_seconds: int | None = None,
    heartbeat_seconds: int = 30,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    emit_progress(progress, f"[full-test-suite] starting loop with manifest {manifest_path}")
    for index in range(1, max_steps + 1):
        preview = next_action(manifest_path)
        if preview["action"] == "blocked":
            emit_progress(progress, f"[full-test-suite] blocked: {preview.get('reason', 'unknown reason')}")
            return {"status": "blocked", "steps": steps, "next_action": preview}
        started = time.monotonic()
        try:
            step_result = execute_step(
                manifest_path=manifest_path,
                codex_binary=codex_binary,
                model=model,
                config_profile=config_profile,
                danger_full_access=danger_full_access,
                progress=progress,
                step_timeout_seconds=step_timeout_seconds,
                heartbeat_seconds=heartbeat_seconds,
            )
        except RuntimeError as exc:
            emit_progress(progress, f"[full-test-suite] step failed: {exc}")
            return {
                "status": "blocked",
                "steps": steps,
                "next_action": preview,
                "error": str(exc),
            }
        elapsed = time.monotonic() - started
        steps.append(step_result)
        emit_progress(progress, f"[full-test-suite] completed action {step_result['action']['action']}")
        emit_progress(progress, summarize_step(manifest_path, index, step_result, elapsed))
        if step_result["action"]["action"] == "finalize":
            emit_progress(progress, "[full-test-suite] run complete")
            return {"status": "completed", "steps": steps, "next_action": {"action": "done"}}

    emit_progress(progress, "[full-test-suite] max steps reached before convergence")
    return {
        "status": "max-steps-reached",
        "steps": steps,
        "next_action": next_action(manifest_path),
    }


def execute_run(
    repo_root: Path,
    findings_path: Path | None,
    report_path: Path | None,
    manifest_path: Path | None,
    scope: str,
    mode: str,
    profile: str,
    codex_binary: str = "codex",
    model: str | None = None,
    config_profile: str | None = None,
    danger_full_access: bool = False,
    max_steps: int = 50,
    reinit: bool = False,
    progress: bool = True,
    preserve_artifacts: bool = False,
    step_timeout_seconds: int | None = None,
    heartbeat_seconds: int = 30,
) -> dict[str, Any]:
    findings_path = findings_path or (repo_root / "project-audit-findings.md")
    report_path = report_path or (repo_root / "full-test-suite-report.md")
    manifest_path = manifest_path or (repo_root / "full-test-suite-manifest.json")

    if reinit or not manifest_path.exists():
        emit_progress(progress, f"[full-test-suite] initializing run in {repo_root}")
        init_run(
            repo_root=repo_root,
            findings_path=findings_path,
            report_path=report_path,
            manifest_path=manifest_path,
            scope=scope,
            mode=mode,
            profile=profile,
            reset_artifacts=reinit and not preserve_artifacts,
        )

    return execute_loop(
        manifest_path=manifest_path,
        codex_binary=codex_binary,
        model=model,
        config_profile=config_profile,
        danger_full_access=danger_full_access,
        max_steps=max_steps,
        progress=progress,
        step_timeout_seconds=step_timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    step_cmd = subparsers.add_parser("step")
    step_cmd.add_argument("--manifest-path", required=True)
    step_cmd.add_argument("--codex-binary", default="codex")
    step_cmd.add_argument("--model")
    step_cmd.add_argument("--config-profile")
    step_cmd.add_argument("--danger-full-access", action="store_true")
    step_cmd.add_argument("--step-timeout-seconds", type=int)
    step_cmd.add_argument("--heartbeat-seconds", type=int, default=30)
    step_cmd.add_argument("--quiet", action="store_true")

    loop_cmd = subparsers.add_parser("loop")
    loop_cmd.add_argument("--manifest-path", required=True)
    loop_cmd.add_argument("--codex-binary", default="codex")
    loop_cmd.add_argument("--model")
    loop_cmd.add_argument("--config-profile")
    loop_cmd.add_argument("--danger-full-access", action="store_true")
    loop_cmd.add_argument("--max-steps", type=int, default=50)
    loop_cmd.add_argument("--step-timeout-seconds", type=int)
    loop_cmd.add_argument("--heartbeat-seconds", type=int, default=30)
    loop_cmd.add_argument("--quiet", action="store_true")

    run_cmd = subparsers.add_parser("run")
    run_cmd.add_argument("--repo-root", required=True)
    run_cmd.add_argument("--findings-path")
    run_cmd.add_argument("--report-path")
    run_cmd.add_argument("--manifest-path")
    run_cmd.add_argument("--scope", default="repo-wide")
    run_cmd.add_argument("--mode", default="default")
    run_cmd.add_argument("--profile", default="core")
    run_cmd.add_argument("--codex-binary", default="codex")
    run_cmd.add_argument("--model")
    run_cmd.add_argument("--config-profile")
    run_cmd.add_argument("--danger-full-access", action="store_true")
    run_cmd.add_argument("--max-steps", type=int, default=50)
    run_cmd.add_argument("--reinit", action="store_true")
    run_cmd.add_argument("--preserve-artifacts", action="store_true")
    run_cmd.add_argument("--step-timeout-seconds", type=int)
    run_cmd.add_argument("--heartbeat-seconds", type=int, default=30)
    run_cmd.add_argument("--quiet", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "step":
        result = execute_step(
            manifest_path=Path(args.manifest_path),
            codex_binary=args.codex_binary,
            model=args.model,
            config_profile=args.config_profile,
            danger_full_access=args.danger_full_access,
            progress=not args.quiet,
            step_timeout_seconds=args.step_timeout_seconds,
            heartbeat_seconds=args.heartbeat_seconds,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "loop":
        result = execute_loop(
            manifest_path=Path(args.manifest_path),
            codex_binary=args.codex_binary,
            model=args.model,
            config_profile=args.config_profile,
            danger_full_access=args.danger_full_access,
            max_steps=args.max_steps,
            progress=not args.quiet,
            step_timeout_seconds=args.step_timeout_seconds,
            heartbeat_seconds=args.heartbeat_seconds,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "run":
        result = execute_run(
            repo_root=Path(args.repo_root),
            findings_path=Path(args.findings_path) if args.findings_path else None,
            report_path=Path(args.report_path) if args.report_path else None,
            manifest_path=Path(args.manifest_path) if args.manifest_path else None,
            scope=args.scope,
            mode=args.mode,
            profile=args.profile,
            codex_binary=args.codex_binary,
            model=args.model,
            config_profile=args.config_profile,
            danger_full_access=args.danger_full_access,
            max_steps=args.max_steps,
            reinit=args.reinit,
            progress=not args.quiet,
            preserve_artifacts=args.preserve_artifacts,
            step_timeout_seconds=args.step_timeout_seconds,
            heartbeat_seconds=args.heartbeat_seconds,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
