#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
ABSOLUTE_PATH_PATTERN = re.compile(r"(/Users/|/private/|\\\\Users\\\\)")
REFERENCE_PATTERN = re.compile(r"`([^`]+/(?:references|scripts)/[^`]+)`")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"{path.relative_to(ROOT)} is missing opening frontmatter delimiter")
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        fail(f"{path.relative_to(ROOT)} is missing closing frontmatter delimiter")

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            fail(f"{path.relative_to(ROOT)} has invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        metadata[key] = value.strip().strip('"')

    allowed = {"name", "description"}
    extra = sorted(set(metadata) - allowed)
    if extra:
        fail(f"{path.relative_to(ROOT)} has nonstandard frontmatter keys: {', '.join(extra)}")
    if not metadata.get("name"):
        fail(f"{path.relative_to(ROOT)} is missing frontmatter name")
    if not metadata.get("description"):
        fail(f"{path.relative_to(ROOT)} is missing frontmatter description")
    if metadata["name"] != path.parent.name:
        fail(f"{path.relative_to(ROOT)} name does not match folder {path.parent.name}")
    return metadata


def validate_references(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for match in REFERENCE_PATTERN.finditer(text):
        raw = match.group(1).split()[0]
        candidate = (path.parent / raw).resolve()
        if not candidate.exists():
            fail(f"{path.relative_to(ROOT)} references missing file {raw}")


def validate_no_absolute_paths() -> None:
    for path in SKILLS_DIR.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8")
            if ABSOLUTE_PATH_PATTERN.search(text):
                fail(f"{path.relative_to(ROOT)} contains a machine-local absolute path")


def run_tests() -> None:
    test_dirs = [
        SKILLS_DIR / "_shared-project-ops" / "scripts" / "tests",
        SKILLS_DIR / "issue-operator" / "scripts" / "tests",
        SKILLS_DIR / "full-test-suite" / "scripts" / "tests",
    ]
    for test_dir in test_dirs:
        if test_dir.exists():
            subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-p", "test_*.py"],
                cwd=ROOT,
                check=True,
            )


def main() -> None:
    if not SKILLS_DIR.exists():
        fail("skills does not exist")

    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        fail("no skill files found")

    for skill_file in skill_files:
        parse_frontmatter(skill_file)
        validate_references(skill_file)
        agents_file = skill_file.parent / "agents" / "openai.yaml"
        if not agents_file.exists():
            fail(f"{skill_file.parent.relative_to(ROOT)} is missing agents/openai.yaml")

    validate_no_absolute_paths()
    run_tests()
    print(f"Validated {len(skill_files)} skills")


if __name__ == "__main__":
    main()
