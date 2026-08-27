#!/usr/bin/env python3
"""Deterministic runner utilities for the full-test-suite skill bundle."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SHARED_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "_shared-project-ops" / "scripts"
if str(SHARED_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_SCRIPTS_DIR))

from project_ops_state import load_findings, load_report, save_findings, save_report, sync_report_from_findings  # noqa: E402

ISSUE_HELPER = Path(__file__).resolve().parents[2] / "issue-operator" / "scripts" / "gh_issue_helper.py"
MANIFEST_VERSION = 1

CORE_SKILLS = [
    "project-health-check",
    "bug-hunter",
    "security-audit-lite",
    "api-contract-auditor",
    "docs-sync",
    "issue-operator",
]

PRE_RELEASE_SKILLS = CORE_SKILLS + [
    "release-readiness",
    "test-gap-finder",
    "dependency-risk-review",
    "refactor-safety-check",
]

DEEP_AUDIT_SKILLS = PRE_RELEASE_SKILLS + [
    "onboarding-doc-builder",
    "observability-gap-review",
    "config-drift-auditor",
    "data-model-migration-review",
    "frontend-regression-review",
]

TYPE_TO_SKILLS = {
    "health": ["project-health-check"],
    "bug": ["bug-hunter"],
    "security": ["security-audit-lite"],
    "api-contract": ["api-contract-auditor"],
    "docs": ["docs-sync"],
    "release": ["release-readiness"],
    "testing": ["test-gap-finder"],
    "dependency": ["dependency-risk-review"],
    "observability": ["observability-gap-review"],
    "config": ["config-drift-auditor", "security-audit-lite"],
    "migration": ["data-model-migration-review", "bug-hunter"],
    "frontend": ["frontend-regression-review", "bug-hunter"],
}


def current_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def backup_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def profile_skills(profile: str) -> list[str]:
    if profile == "core":
        return CORE_SKILLS
    if profile == "pre-release":
        return PRE_RELEASE_SKILLS
    if profile == "deep-audit":
        return DEEP_AUDIT_SKILLS
    raise ValueError(f"Unsupported profile: {profile}")


def git_output(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def repo_context(repo_root: Path) -> dict[str, str]:
    branch = git_output(repo_root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    dirty = "yes" if (git_output(repo_root, "status", "--short") or "").strip() else "no"
    github_sync = "available" if shutil.which("gh") else "unavailable"
    return {
        "branch": branch,
        "dirty_worktree": dirty,
        "github_sync": github_sync,
    }


def infer_skills_from_surface(surface: str, available: set[str]) -> list[str]:
    inferred: list[str] = []

    def add(skill: str) -> None:
        if skill in available and skill not in inferred:
            inferred.append(skill)

    if any(marker in surface for marker in ("readme", "agents.md", ".md", "docs/")):
        add("docs-sync")
    if any(marker in surface for marker in ("openapi", "contract", "schema", "graphql", "/routes/", "api/", "dto")):
        add("api-contract-auditor")
    if any(marker in surface for marker in ("secret", "token", "auth", "permission", "role", "env", ".github", "ci", "config")):
        add("security-audit-lite")
        add("config-drift-auditor")
        add("project-health-check")
    if any(marker in surface for marker in ("migration", "schema", "sqlite", "coredata", "persistence", "database", "backfill")):
        add("data-model-migration-review")
        add("bug-hunter")
    if any(marker in surface for marker in ("swiftui", "view", "ui", "frontend", "layout", "watch app", "liveactivities")):
        add("frontend-regression-review")
        add("bug-hunter")
    if any(marker in surface for marker in ("test", "spec")):
        add("test-gap-finder")
        add("bug-hunter")
    if any(marker in surface for marker in ("package", "podfile", "package.json", "package-lock", "pnpm-lock", "yarn.lock")):
        add("dependency-risk-review")
        add("project-health-check")
    if any(marker in surface for marker in ("release", "rollout", "flag", "changelog")):
        add("release-readiness")
    if any(marker in surface for marker in ("log", "metric", "trace", "telemetry", "observability")):
        add("observability-gap-review")
    if not inferred:
        add("bug-hunter")
        add("project-health-check")

    return inferred


def suggest_rerun(profile: str, surfaces: list[str], finding_types: list[str]) -> dict[str, Any]:
    available = set(profile_skills(profile))
    requested: list[str] = []

    for finding_type in finding_types:
        for skill in TYPE_TO_SKILLS.get(finding_type, []):
            if skill in available and skill not in requested:
                requested.append(skill)

    for surface in surfaces:
        normalized = surface.lower()
        inferred = infer_skills_from_surface(normalized, available)
        for skill in inferred:
            if skill not in requested:
                requested.append(skill)

    if requested and "issue-operator" in available and "issue-operator" not in requested:
        requested.append("issue-operator")
    return {"skills": requested}


def default_manifest_path(report_path: Path) -> Path:
    return report_path.with_name("full-test-suite-manifest.json")


def archive_artifact(path: Path, timestamp_tag: str) -> str | None:
    if not path.exists():
        return None
    backup_path = path.with_name(f"{path.name}.bak-{timestamp_tag}")
    counter = 1
    while backup_path.exists():
        backup_path = path.with_name(f"{path.name}.bak-{timestamp_tag}-{counter}")
        counter += 1
    path.replace(backup_path)
    return str(backup_path)


def init_manifest(
    manifest_path: Path,
    repo_root: Path,
    findings_path: Path,
    report_path: Path,
    scope: str,
    mode: str,
    profile: str,
) -> dict[str, Any]:
    timestamp = current_timestamp()
    skills = profile_skills(profile)
    manifest = {
        "version": MANIFEST_VERSION,
        "status": "active",
        "mode": mode,
        "profile": profile,
        "scope": scope,
        "repo_root": str(repo_root),
        "findings_path": str(findings_path),
        "report_path": str(report_path),
        "selected_skills": skills,
        "created_at": timestamp,
        "updated_at": timestamp,
        "current_cycle": 1,
        "pending_issue_sync": False,
        "requires_clean_full_scan": False,
        "awaiting_clean_scan_result": False,
        "clean_full_scan_streak": 0,
        "fixes_applied": 0,
        "cycles": [
            {
                "id": 1,
                "kind": "full-scan",
                "origin": "initial",
                "started_at": timestamp,
                "completed_at": None,
                "pending_skills": list(skills),
                "completed": [],
            }
        ],
        "fix_history": [],
        "issue_sync_history": [],
        "history": [
            {
                "timestamp": timestamp,
                "type": "run-initialized",
                "details": {
                    "profile": profile,
                    "mode": mode,
                    "scope": scope,
                },
            }
        ],
    }
    save_manifest(manifest_path, manifest)
    return manifest


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def save_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = current_timestamp()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_history(manifest: dict[str, Any], event_type: str, details: dict[str, Any]) -> None:
    manifest.setdefault("history", []).append(
        {
            "timestamp": current_timestamp(),
            "type": event_type,
            "details": details,
        }
    )


def current_cycle(manifest: dict[str, Any]) -> dict[str, Any] | None:
    for cycle in reversed(manifest.get("cycles", [])):
        if cycle.get("completed_at") is None:
            return cycle
    return None


def create_cycle(manifest: dict[str, Any], kind: str, origin: str, skills: list[str]) -> dict[str, Any]:
    if not skills:
        raise ValueError("Cannot create an empty cycle.")
    cycle_id = manifest.get("current_cycle", 0) + 1
    manifest["current_cycle"] = cycle_id
    cycle = {
        "id": cycle_id,
        "kind": kind,
        "origin": origin,
        "started_at": current_timestamp(),
        "completed_at": None,
        "pending_skills": list(skills),
        "completed": [],
    }
    manifest.setdefault("cycles", []).append(cycle)
    append_history(manifest, "cycle-created", {"id": cycle_id, "kind": kind, "origin": origin, "skills": skills})
    return cycle


def init_run(
    repo_root: Path,
    findings_path: Path,
    report_path: Path,
    scope: str,
    mode: str,
    profile: str,
    manifest_path: Path | None = None,
    reset_artifacts: bool = False,
) -> dict[str, Any]:
    context = repo_context(repo_root)
    timestamp = current_timestamp()
    manifest_path = manifest_path or default_manifest_path(report_path)
    archived_artifacts: dict[str, str] = {}

    if reset_artifacts:
        tag = backup_timestamp()
        for label, path in (
            ("findings", findings_path),
            ("report", report_path),
            ("manifest", manifest_path),
        ):
            archived = archive_artifact(path, tag)
            if archived is not None:
                archived_artifacts[label] = archived

    findings = load_findings(findings_path)
    findings.summary.update(
        {
            "Audit date": timestamp,
            "Scope": scope,
            "Branch": context["branch"],
            "GitHub issue sync": context["github_sync"],
            "Final state": findings.final_state(),
        }
    )
    save_findings(findings_path, findings)

    report = load_report(report_path)
    report.summary.update(
        {
            "Mode": mode,
            "Profile": profile,
            "Scope": scope,
            "Branch": context["branch"],
            "Dirty worktree": context["dirty_worktree"],
            "GitHub issue sync": context["github_sync"],
            "Updated at": timestamp,
        }
    )
    for skill in profile_skills(profile):
        if not any(item["name"] == skill for item in report.skills_run):
            report.upsert_skill(skill, "pending")
    sync_report_from_findings(report, findings, timestamp)
    save_report(report_path, report)

    manifest = init_manifest(
        manifest_path=manifest_path,
        repo_root=repo_root,
        findings_path=findings_path,
        report_path=report_path,
        scope=scope,
        mode=mode,
        profile=profile,
    )

    return {
        "repo_root": str(repo_root),
        "findings_path": str(findings_path),
        "report_path": str(report_path),
        "manifest_path": str(manifest_path),
        "archived_artifacts": archived_artifacts,
        "skills": profile_skills(profile),
        "summary": report.summary,
        "next_action": next_action(manifest_path),
    }


def record_skill(
    report_path: Path,
    skill: str,
    status: str,
    note: str | None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    report = load_report(report_path)
    report.upsert_skill(skill, status, note)
    report.summary["Updated at"] = current_timestamp()
    save_report(report_path, report)

    payload = {"report_path": str(report_path), "skill": skill, "status": status, "note": note or ""}
    if manifest_path is not None:
        manifest = load_manifest(manifest_path)
        cycle = current_cycle(manifest)
        if cycle is None:
            raise ValueError("No active cycle to record skill against.")
        if skill in cycle["pending_skills"]:
            cycle["pending_skills"].remove(skill)
        cycle["completed"].append(
            {
                "name": skill,
                "status": status,
                "note": note or "",
                "timestamp": current_timestamp(),
            }
        )
        append_history(manifest, "skill-recorded", {"cycle": cycle["id"], "skill": skill, "status": status, "note": note or ""})
        if not cycle["pending_skills"]:
            cycle["completed_at"] = current_timestamp()
            manifest["pending_issue_sync"] = True
            append_history(manifest, "cycle-completed", {"cycle": cycle["id"], "kind": cycle["kind"]})
        save_manifest(manifest_path, manifest)
        payload["manifest_path"] = str(manifest_path)
        payload["next_action"] = next_action(manifest_path)
    return payload


def plan_fixes(findings_path: Path, report_path: Path | None = None) -> dict[str, Any]:
    findings = load_findings(findings_path)
    queue = findings.build_fix_queue(["confirmed-open", "in-progress"])
    if report_path is not None:
        report = load_report(report_path)
        sync_report_from_findings(report, findings, current_timestamp())
        save_report(report_path, report)
    return {"queue": queue}


def record_verification(report_path: Path, item: str) -> dict[str, Any]:
    report = load_report(report_path)
    report.append_unique("verification", item)
    report.summary["Updated at"] = current_timestamp()
    save_report(report_path, report)
    return {"report_path": str(report_path), "verification": report.verification}


def record_issue_activity(report_path: Path, created: list[str], updated: list[str], closed: list[str]) -> dict[str, Any]:
    report = load_report(report_path)
    for issue_id in created:
        report.add_issue_activity("Created", issue_id)
    for issue_id in updated:
        report.add_issue_activity("Updated", issue_id)
    for issue_id in closed:
        report.add_issue_activity("Closed", issue_id)
    report.summary["Updated at"] = current_timestamp()
    save_report(report_path, report)
    return {"report_path": str(report_path), "issue_activity": report.issue_activity}


def record_fix(
    manifest_path: Path,
    finding_id: str,
    surfaces: list[str],
    finding_types: list[str],
    note: str | None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    rerun = suggest_rerun(manifest["profile"], surfaces, finding_types)["skills"]
    manifest["fixes_applied"] = manifest.get("fixes_applied", 0) + 1
    manifest["requires_clean_full_scan"] = True
    manifest["clean_full_scan_streak"] = 0
    manifest.setdefault("fix_history", []).append(
        {
            "finding_id": finding_id,
            "surfaces": surfaces,
            "finding_types": finding_types,
            "note": note or "",
            "timestamp": current_timestamp(),
        }
    )
    append_history(
        manifest,
        "fix-recorded",
        {
            "finding_id": finding_id,
            "surfaces": surfaces,
            "finding_types": finding_types,
            "rerun_skills": rerun,
            "note": note or "",
        },
    )
    if rerun:
        create_cycle(manifest, "rerun", f"post-fix:{finding_id}", rerun)
    save_manifest(manifest_path, manifest)
    return {
        "manifest_path": str(manifest_path),
        "finding_id": finding_id,
        "rerun_skills": rerun,
        "next_action": next_action(manifest_path),
    }


def record_issue_sync(manifest_path: Path, result_payload: dict[str, Any]) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    manifest["pending_issue_sync"] = False
    manifest.setdefault("issue_sync_history", []).append(
        {
            "timestamp": current_timestamp(),
            "result": result_payload,
        }
    )
    append_history(manifest, "issue-sync-recorded", result_payload)
    save_manifest(manifest_path, manifest)
    return {"manifest_path": str(manifest_path), "result": result_payload, "next_action": next_action(manifest_path)}


def run_issue_sync(
    manifest_path: Path,
    repo: str | None = None,
    gh_binary: str = "gh",
    dry_run: bool = False,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    command = [
        "python3",
        str(ISSUE_HELPER),
        "sync",
        "--repo-root",
        manifest["repo_root"],
        "--findings-path",
        manifest["findings_path"],
        "--report-path",
        manifest["report_path"],
        "--gh-binary",
        gh_binary,
    ]
    if repo:
        command.extend(["--repo", repo])
    if dry_run:
        command.append("--dry-run")

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Issue sync failed.")
    payload = json.loads(result.stdout)
    return record_issue_sync(manifest_path, payload)


def schedule_full_scan_if_needed(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    if current_cycle(manifest) is not None:
        return manifest
    if manifest.get("pending_issue_sync"):
        return manifest
    if manifest.get("requires_clean_full_scan"):
        create_cycle(manifest, "full-scan", "post-fix-validation", manifest["selected_skills"])
        manifest["requires_clean_full_scan"] = False
        manifest["awaiting_clean_scan_result"] = True
        save_manifest(manifest_path, manifest)
    return manifest


def next_action(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    findings = load_findings(Path(manifest["findings_path"]))
    report = load_report(Path(manifest["report_path"]))
    queue = findings.build_fix_queue(["confirmed-open", "in-progress"])
    cycle = current_cycle(manifest)

    if cycle is not None and cycle["pending_skills"]:
        skill = cycle["pending_skills"][0]
        return {
            "action": "run-skill",
            "skill": skill,
            "cycle": cycle["id"],
            "cycle_kind": cycle["kind"],
            "reason": f"Pending {cycle['kind']} skill in cycle {cycle['id']}.",
        }

    if manifest.get("pending_issue_sync"):
        sync_state = report.summary.get("GitHub issue sync")
        return {
            "action": "sync-issues",
            "reason": "A scan or rerun cycle completed and issue reconciliation is pending.",
            "github_issue_sync": sync_state,
        }

    manifest = schedule_full_scan_if_needed(manifest_path)
    cycle = current_cycle(manifest)
    if cycle is not None and cycle["pending_skills"]:
        skill = cycle["pending_skills"][0]
        return {
            "action": "run-skill",
            "skill": skill,
            "cycle": cycle["id"],
            "cycle_kind": cycle["kind"],
            "reason": f"Pending {cycle['kind']} skill in cycle {cycle['id']}.",
        }

    if queue and manifest["mode"] != "scan-only":
        finding = queue[0]
        return {
            "action": "fix-finding",
            "finding": finding,
            "reason": "Confirmed actionable findings remain; fix the next highest-priority item.",
        }

    if queue and manifest["mode"] == "scan-only":
        return {
            "action": "finalize",
            "reason": "Scan-only mode is complete; confirmed findings remain for later handling.",
        }

    if manifest.get("awaiting_clean_scan_result"):
        manifest["awaiting_clean_scan_result"] = False
        manifest["clean_full_scan_streak"] = manifest.get("clean_full_scan_streak", 0) + 1
        append_history(
            manifest,
            "clean-scan-confirmed",
            {"clean_full_scan_streak": manifest["clean_full_scan_streak"]},
        )
        save_manifest(manifest_path, manifest)

    if not queue:
        return {
            "action": "finalize",
            "reason": "No confirmed-open or in-progress findings remain and no pending cycles remain.",
        }

    return {
        "action": "blocked",
        "reason": "The runner could not determine a safe next step from the current manifest state.",
    }


def finalize_run(repo_root: Path, findings_path: Path, report_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    findings = load_findings(findings_path)
    report = load_report(report_path)
    context = repo_context(repo_root)
    report.summary.update(
        {
            "Branch": context["branch"],
            "Dirty worktree": context["dirty_worktree"],
            "GitHub issue sync": context["github_sync"],
        }
    )
    findings.summary.update(
        {
            "Branch": context["branch"],
            "GitHub issue sync": context["github_sync"],
        }
    )
    timestamp = current_timestamp()
    findings.summary["Final state"] = findings.final_state()
    report.summary["Updated at"] = timestamp
    sync_report_from_findings(report, findings, timestamp)
    save_findings(findings_path, findings)
    save_report(report_path, report)

    payload = {
        "findings_path": str(findings_path),
        "report_path": str(report_path),
        "final_state": report.summary["Final state"],
        "remaining_items": report.remaining_items,
    }

    if manifest_path is not None:
        manifest = load_manifest(manifest_path)
        manifest["status"] = "completed"
        append_history(manifest, "run-finalized", {"final_state": report.summary["Final state"]})
        save_manifest(manifest_path, manifest)
        payload["manifest_path"] = str(manifest_path)

    return payload


def show_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    return {
        "manifest": manifest,
        "next_action": next_action(manifest_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init")
    init_cmd.add_argument("--repo-root", required=True)
    init_cmd.add_argument("--findings-path", required=True)
    init_cmd.add_argument("--report-path", required=True)
    init_cmd.add_argument("--manifest-path")
    init_cmd.add_argument("--scope", required=True)
    init_cmd.add_argument("--mode", default="default")
    init_cmd.add_argument("--profile", default="core")
    init_cmd.add_argument("--reset-artifacts", action="store_true")

    record_skill_cmd = subparsers.add_parser("record-skill")
    record_skill_cmd.add_argument("--report-path", required=True)
    record_skill_cmd.add_argument("--manifest-path")
    record_skill_cmd.add_argument("--skill", required=True)
    record_skill_cmd.add_argument("--status", required=True)
    record_skill_cmd.add_argument("--note")

    plan_fixes_cmd = subparsers.add_parser("plan-fixes")
    plan_fixes_cmd.add_argument("--findings-path", required=True)
    plan_fixes_cmd.add_argument("--report-path")

    verification_cmd = subparsers.add_parser("record-verification")
    verification_cmd.add_argument("--report-path", required=True)
    verification_cmd.add_argument("--item", required=True)

    issue_cmd = subparsers.add_parser("record-issue-activity")
    issue_cmd.add_argument("--report-path", required=True)
    issue_cmd.add_argument("--created", action="append", default=[])
    issue_cmd.add_argument("--updated", action="append", default=[])
    issue_cmd.add_argument("--closed", action="append", default=[])

    rerun_cmd = subparsers.add_parser("suggest-rerun")
    rerun_cmd.add_argument("--profile", default="core")
    rerun_cmd.add_argument("--surfaces", default="")
    rerun_cmd.add_argument("--types", default="")

    fix_cmd = subparsers.add_parser("record-fix")
    fix_cmd.add_argument("--manifest-path", required=True)
    fix_cmd.add_argument("--finding-id", required=True)
    fix_cmd.add_argument("--surfaces", default="")
    fix_cmd.add_argument("--types", default="")
    fix_cmd.add_argument("--note")

    next_cmd = subparsers.add_parser("next-action")
    next_cmd.add_argument("--manifest-path", required=True)

    sync_issues_cmd = subparsers.add_parser("sync-issues")
    sync_issues_cmd.add_argument("--manifest-path", required=True)
    sync_issues_cmd.add_argument("--repo")
    sync_issues_cmd.add_argument("--gh-binary", default="gh")
    sync_issues_cmd.add_argument("--dry-run", action="store_true")

    issue_sync_record_cmd = subparsers.add_parser("record-issue-sync")
    issue_sync_record_cmd.add_argument("--manifest-path", required=True)
    issue_sync_record_cmd.add_argument("--payload", required=True)

    show_manifest_cmd = subparsers.add_parser("show-manifest")
    show_manifest_cmd.add_argument("--manifest-path", required=True)

    finalize_cmd = subparsers.add_parser("finalize")
    finalize_cmd.add_argument("--repo-root", required=True)
    finalize_cmd.add_argument("--findings-path", required=True)
    finalize_cmd.add_argument("--report-path", required=True)
    finalize_cmd.add_argument("--manifest-path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        result = init_run(
            repo_root=Path(args.repo_root),
            findings_path=Path(args.findings_path),
            report_path=Path(args.report_path),
            manifest_path=Path(args.manifest_path) if args.manifest_path else None,
            scope=args.scope,
            mode=args.mode,
            profile=args.profile,
            reset_artifacts=args.reset_artifacts,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "record-skill":
        result = record_skill(
            Path(args.report_path),
            args.skill,
            args.status,
            args.note,
            Path(args.manifest_path) if args.manifest_path else None,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "plan-fixes":
        result = plan_fixes(Path(args.findings_path), Path(args.report_path) if args.report_path else None)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "record-verification":
        result = record_verification(Path(args.report_path), args.item)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "record-issue-activity":
        result = record_issue_activity(Path(args.report_path), args.created, args.updated, args.closed)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "suggest-rerun":
        surfaces = [item.strip() for item in args.surfaces.split(",") if item.strip()]
        types = [item.strip() for item in args.types.split(",") if item.strip()]
        result = suggest_rerun(args.profile, surfaces, types)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "record-fix":
        surfaces = [item.strip() for item in args.surfaces.split(",") if item.strip()]
        types = [item.strip() for item in args.types.split(",") if item.strip()]
        result = record_fix(Path(args.manifest_path), args.finding_id, surfaces, types, args.note)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "next-action":
        result = next_action(Path(args.manifest_path))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "sync-issues":
        result = run_issue_sync(Path(args.manifest_path), repo=args.repo, gh_binary=args.gh_binary, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "record-issue-sync":
        result = record_issue_sync(Path(args.manifest_path), json.loads(args.payload))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "show-manifest":
        result = show_manifest(Path(args.manifest_path))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "finalize":
        result = finalize_run(
            Path(args.repo_root),
            Path(args.findings_path),
            Path(args.report_path),
            Path(args.manifest_path) if args.manifest_path else None,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
