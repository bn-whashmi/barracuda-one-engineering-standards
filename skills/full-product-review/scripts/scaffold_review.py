#!/usr/bin/env python3
"""Create a standardized full-product-review folder and markdown templates."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys


def build_templates(review_date: str, product_name: str, scope: str, folder_rel: str) -> dict[str, str]:
    title = f"Full Product Review - {review_date}"
    return {
        "00-index.md": f"""# {title}

This folder is the source of truth for the {review_date} full product review.

## Scope
- Product: {product_name}
- Scope: {scope}
- Branch: [fill]

## Artifacts
- Executive summary: `{folder_rel}/10-executive-summary.md`
- Scorecard: `{folder_rel}/20-scorecard.md`
- Findings ledger: `{folder_rel}/30-findings-ledger.md`
- Structural issues: `{folder_rel}/40-structural-issues.md`
- Priority plan: `{folder_rel}/50-priority-plan.md`

## Evidence Sources Used
- [repo paths, docs, issues, incidents, analytics, or operator notes]
""",
        "10-executive-summary.md": f"""# Executive Summary - {review_date}

Findings summary (from {folder_rel}):
Overall posture: Product ?/5, Reliability ?/5, Security/Tenant ?/5, Delivery ?/5, Cost ?/5.
Resolved: none.
Partially resolved: none.
Open P0/P1 risks: [fill].
Working well: [fill].
Structural issues to revisit: [fill].
Underlying technical issues: [fill].
Recommended sequence: [fill].
Major re-architecture: not recommended now because [fill].

## Top Strengths
- [fill]

## Open P0/P1 Risks
- [fill]

## Structural Issues To Revisit
- [fill]

## Underlying Technical Issues
- [fill]

## Near-Term Recommendation
- [fill]

## Major-Work Gate
- Trigger: [fill]
- Evidence required: [fill]
""",
        "20-scorecard.md": f"""# Current State Scorecard - {review_date}

Scoring: 1 (poor) to 5 (excellent). Use the review rubric and avoid inflated scores.

## Product (?/5)
**Working**
- [fill]

**Needs improvement**
- [fill]

## Reliability (?/5)
**Working**
- [fill]

**Needs improvement**
- [fill]

## Security/Tenant (?/5)
**Working**
- [fill]

**Needs improvement**
- [fill]

## Delivery (?/5)
**Working**
- [fill]

**Needs improvement**
- [fill]

## Cost (?/5)
**Working**
- [fill]

**Needs improvement**
- [fill]
""",
        "30-findings-ledger.md": f"""# Findings Ledger - {review_date}

Purpose: reconcile product, technical, and operational findings against current evidence and define the smallest credible next actions.

| ID | Theme | Priority | Status | Confidence | Surface | Evidence | Impact | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [fill] | [product/reliability/security/delivery/cost/architecture] | [P0-P3] | [Open/Partially Resolved/Resolved/Needs Re-check/Deferred/Obsolete] | [High/Medium/Low] | [subsystem] | [repo evidence] | [user/business/ops impact] | [smallest next step] |
""",
        "40-structural-issues.md": f"""# Structural Issues - {review_date}

Document the root causes and architecture decisions that explain the current posture.

## Preserve As-Is
- [strengths worth keeping]

## Revisit Now
- [structural issue + evidence + smallest corrective move]

## Defer Unless Trigger Fires
- [major work that is not justified yet]

## Evidence Gaps Or Open Questions
- [missing signal, missing metric, or unresolved ambiguity]
""",
        "50-priority-plan.md": f"""# 0-30-60-90 Plan - {review_date}

## 0-30 Days
- Action: [fill]
  - Outcome/KPI: [fill]
  - Dependency: [fill if needed]

## 31-60 Days
- Action: [fill]
  - Outcome/KPI: [fill]
  - Dependency: [fill if needed]

## 61-90 Days
- Action: [fill]
  - Outcome/KPI: [fill]
  - Dependency: [fill if needed]

## Major-Work Trigger
- Trigger: [fill]
- Evidence required: [fill]
""",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root where docs/reviews lives.")
    parser.add_argument("--product-name", help="Human-readable product name. Defaults to the repo directory name.")
    parser.add_argument("--scope", default="repo-wide", help="Short scope label for the review.")
    parser.add_argument("--slug", default="full-product-review", help="Folder slug prefix.")
    parser.add_argument("--review-date", default=date.today().isoformat(), help="Review date in YYYY-MM-DD.")
    parser.add_argument("--output-subdir", default="docs/reviews", help="Output directory relative to repo root.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing review folder.")
    return parser.parse_args()


def write_review_pack(args: argparse.Namespace) -> Path:
    repo_root = Path(args.repo_root).resolve()
    product_name = args.product_name or repo_root.name
    review_dir = repo_root / args.output_subdir / f"{args.slug}-{args.review_date}"
    folder_rel = review_dir.relative_to(repo_root).as_posix()

    if review_dir.exists() and not args.force:
        raise FileExistsError(f"Review folder already exists: {review_dir}")

    review_dir.mkdir(parents=True, exist_ok=True)
    templates = build_templates(args.review_date, product_name, args.scope, folder_rel)
    for filename, content in templates.items():
        (review_dir / filename).write_text(content)
    return review_dir


def main() -> int:
    args = parse_args()
    try:
        review_dir = write_review_pack(args)
    except FileExistsError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(review_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
