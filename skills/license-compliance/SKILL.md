---
name: license-compliance
description: "Audit and fix license posture across repository roots, package metadata, vendored exceptions, and generated artifacts. Use when asked to ensure repos have valid LICENSE files, align package license declarations, or distinguish first-party code from vendored third-party code."
---

# License Compliance

Use this skill for repository license and package metadata work.

## Workflow

1. Inventory root `LICENSE`, package manifests, vendored directories, generated package examples, and archived repositories.
2. Classify each hit as first-party, vendored third-party, generated sample, or external dependency fixture.
3. For first-party code, align the root license, package metadata, and repository visibility.
4. Leave vendored third-party package metadata intact unless the user explicitly asks to modify vendored code.
5. Verify the final scan excludes vendored and dependency directories.

## Standards

- Root repositories include an explicit `LICENSE` file.
- First-party package metadata matches the selected license and whether the package is publishable.
- Third-party vendored packages keep their original license metadata.
- Public repositories still need an explicit license decision; do not assume open source or private by default.

## Safety

- Do not delete license files to hide a GitHub license badge.
- Do not replace third-party license declarations in vendored package manifests.
- Do not claim legal completeness; surface cases that need attorney review.

## Verification

- Re-scan root `LICENSE` files across active repositories.
- Re-scan first-party package manifests for inconsistent license, visibility, or publishability metadata.
- Report excluded vendored paths explicitly.
