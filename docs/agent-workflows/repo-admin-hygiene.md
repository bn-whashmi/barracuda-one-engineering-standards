# Repo Admin Hygiene Workflow

Use this workflow for repository metadata and GitHub settings cleanup.

## Inspect

- Description and homepage.
- Topics.
- Root `LICENSE`.
- Default branch.
- Wiki and Projects settings.
- Issue and PR templates.
- Standard labels.
- Branch protection or rulesets.

## Apply

- Keep descriptions product-specific.
- Use verified public URLs only.
- Keep `main` as default branch.
- Disable Wikis and per-repo Projects unless intentionally used.
- Use the standard label set from `labels/standard-labels.json`.
- Use the selected license text for the repository.

## Verify

- Re-read GitHub metadata after changes.
- Confirm no blank descriptions on active repos.
- Confirm no non-standard labels remain.
- Confirm each repo has a root `LICENSE`.
