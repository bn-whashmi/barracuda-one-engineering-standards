#!/usr/bin/env python3
"""Claude adapter for the provider-neutral AI PR review workflows.

Contract (docs/ai-review-adapter-setup.md):
  input env:
    AI_REVIEW_ROLE        engineering | qa | security | repo-standards
    AI_REVIEW_RESULT      path to write the findings JSON
    ANTHROPIC_API_KEY     required
    ANTHROPIC_BASE_URL    optional (defaults to https://api.anthropic.com)
    AI_REVIEW_MODEL       optional model override
    GH_TOKEN / GITHUB_*   used to fetch the PR diff via the GitHub API;
                          falls back to `git diff origin/<base>...HEAD`
  output:
    JSON object {"findings": [...]} written to AI_REVIEW_RESULT, one
    finding per root cause, per pr-review/references/finding-format.md
  exit codes:
    0 review completed (findings may exist — blocking is enforced by the
      consolidation job, not the adapter)
    1 adapter failure (no valid result produced)
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROLE = os.environ.get("AI_REVIEW_ROLE", "engineering")
RESULT_PATH = os.environ.get("AI_REVIEW_RESULT", ".ai-review/results/result.json")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BASE_URL = (os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/")
MODEL = os.environ.get("AI_REVIEW_MODEL", "claude-sonnet-4-5")
MAX_DIFF_CHARS = int(os.environ.get("AI_REVIEW_MAX_DIFF_CHARS", "160000"))
MAX_CONTEXT_CHARS_PER_FILE = 9000

ROLE_FOCUS = {
    "engineering": (
        "Engineering lens: functional correctness, architecture and design "
        "consistency, error handling, performance and concurrency, backward "
        "compatibility (especially GraphQL schemas and API contracts), data "
        "integrity and migration safety, maintainability, regression risk, "
        "and oversized/multi-concern changes that should be split."
    ),
    "qa": (
        "QA lens: changed behavior without tests, missing regression tests "
        "for bug fixes, uncovered edge cases and failure paths, weak or "
        "coverage-only assertions, and missing integration/contract/UI "
        "tests where unit tests are insufficient."
    ),
    "security": (
        "Security lens: authentication and authorization, account isolation "
        "(every account-data query filtered by bcc_account_id and access "
        "authorized against the caller's BCC account hierarchy), injection "
        "and unsafe query construction, secret and PII exposure in code or "
        "logs, unsafe deserialization, disabled TLS validation, privilege "
        "escalation, and unauthenticated administrative endpoints."
    ),
    "repo-standards": (
        "Repository standards lens: violations of this repository's ground "
        "truth (CLAUDE.md, AGENTS.md, architecture docs) and platform "
        "conventions. Report missing ground-truth documentation as a "
        "single P3 gap; never invent rules."
    ),
}

CONTEXT_FILES = [
    "pr-review/barracuda-context.md",
    "pr-review/references/finding-format.md",
    ".github/copilot-instructions.md",
    "CLAUDE.md",
    "AGENTS.md",
]


def log(message):
    print(f"ai-review-adapter: {message}", file=sys.stderr)


def fail(message):
    log(message)
    sys.exit(1)


def fetch_pr_diff_from_github():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not (token and event_path and repo and os.path.isfile(event_path)):
        return None
    with open(event_path, encoding="utf-8") as handle:
        event = json.load(handle)
    number = (event.get("pull_request") or {}).get("number")
    if not number:
        return None
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{number}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3.diff",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.URLError as error:
        log(f"GitHub diff fetch failed ({error}); falling back to git diff")
        return None


def fetch_diff_from_git():
    base = os.environ.get("AI_REVIEW_BASE", "origin/main")
    result = subprocess.run(
        ["git", "diff", f"{base}...HEAD"], capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout
    return None


def load_repo_context():
    sections = []
    for path in CONTEXT_FILES:
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as handle:
                content = handle.read()[:MAX_CONTEXT_CHARS_PER_FILE]
            sections.append(f"--- {path} ---\n{content}")
    return "\n\n".join(sections)


def build_system_prompt():
    return (
        "You are an expert code reviewer for the Barracuda Nexus / "
        "BarracudaONE platform performing ONE review lens on a pull "
        f"request.\n\n{ROLE_FOCUS.get(ROLE, ROLE_FOCUS['engineering'])}\n\n"
        "Rules:\n"
        "- Report only material findings; prioritize impact over volume.\n"
        "- One finding per distinct root cause, concrete enough to "
        "reproduce, fix, and verify.\n"
        "- Severities: P0/P1 = material blocking defects only; P2 = should "
        "fix near merge; P3 = recommendation. Never use P0/P1 for style.\n"
        "- Respect the platform's intentional patterns described in the "
        "provided context (fail-open Redis/Intercom, production error "
        "masking, gateway-delegated JWT validation, MSP account-hierarchy "
        "traversal). Do not flag them.\n"
        "- Output ONLY a JSON object, no prose and no code fences, shaped "
        "exactly as:\n"
        '{"findings": [{"id": "ENG-001", "severity": "P2", "status": '
        '"open", "blocking": false, "title": "...", "surface": "...", '
        '"evidence": ["path/to/file.cs:42"], "impact": "...", "fixPlan": '
        '"...", "verification": {"method": "...", "command": "...", '
        '"result": "pending", "residualRisk": ""}}]}\n'
        '- If there are no material findings, output {"findings": []}.'
    )


def call_claude(system_prompt, user_content):
    payload = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 8000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/v1/messages",
        data=payload,
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                body = json.loads(response.read().decode("utf-8"))
            return "".join(
                block.get("text", "")
                for block in body.get("content", [])
                if block.get("type") == "text"
            )
        except urllib.error.HTTPError as error:
            last_error = f"HTTP {error.code}: {error.read().decode('utf-8', 'replace')[:500]}"
            if error.code not in (429, 500, 502, 503, 529):
                break
        except urllib.error.URLError as error:
            last_error = str(error)
        time.sleep(10 * (attempt + 1))
    fail(f"Claude API call failed: {last_error}")


def parse_findings(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        fail(f"model output contained no JSON object: {cleaned[:300]}")
    parsed = json.loads(cleaned[start : end + 1])
    findings = parsed.get("findings")
    if not isinstance(findings, list):
        fail("model output missing a findings array")
    prefix = {"engineering": "ENG", "qa": "QA", "security": "SEC", "repo-standards": "STD"}.get(ROLE, "REV")
    normalized = []
    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            continue
        finding.setdefault("id", f"{prefix}-{index:03d}")
        finding.setdefault("severity", "P3")
        finding.setdefault("status", "open")
        finding.setdefault("blocking", finding.get("severity") in ("P0", "P1"))
        finding.setdefault("evidence", [])
        normalized.append(finding)
    return normalized


def main():
    if not API_KEY:
        fail("ANTHROPIC_API_KEY is not set")
    diff = fetch_pr_diff_from_github() or fetch_diff_from_git()
    if not diff:
        fail("could not obtain a PR diff (GitHub API and git diff both empty)")
    truncated = len(diff) > MAX_DIFF_CHARS
    if truncated:
        diff = diff[:MAX_DIFF_CHARS]
    context = load_repo_context()
    user_content = (
        (f"Repository and platform context:\n\n{context}\n\n" if context else "")
        + "Unified diff of the pull request"
        + (" (TRUNCATED — note incomplete coverage in a P3 finding)" if truncated else "")
        + f":\n\n{diff}"
    )
    findings = parse_findings(call_claude(build_system_prompt(), user_content))
    os.makedirs(os.path.dirname(RESULT_PATH) or ".", exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump({"role": ROLE, "model": MODEL, "findings": findings}, handle, indent=2)
    by_severity = {}
    for finding in findings:
        by_severity[finding["severity"]] = by_severity.get(finding["severity"], 0) + 1
    log(f"role={ROLE} findings={len(findings)} {by_severity or ''}")


if __name__ == "__main__":
    main()
