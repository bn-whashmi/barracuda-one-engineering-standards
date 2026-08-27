# Ruleset Import Notes

The [architecture diagrams](../docs/architecture.md) show the difference
between a ruleset template and an active merge gate. The [control status
guide](../docs/control-status.md) lists the setup required before activation.

`default-branch-protection.json` is an import-oriented repository ruleset
template for baseline PR protection. This canonical repository has an active `main-safety` ruleset using
the checks produced by its own validation workflow. GitHub rulesets are still
repository configuration: each consuming organization must review and create
the template in the target repository.

## Required status checks are opt-in

The default JSON intentionally omits the `required_status_checks` rule. GitHub's
ruleset API rejects that rule when its context list is empty. The template
therefore enforces pull requests, conversation resolution, force-push
prevention, and branch-deletion prevention without inventing contexts for
producers that may not be activated in a consuming repository.

Add a `required_status_checks` rule and status context only after all of the
following are true:

1. The producer is activated in the consuming repository.
2. The exact check has run on a representative pull request.
3. The check reports a real pass/fail result, not a configuration or skipped
   state.
4. The team has chosen `enforced` mode for that control.

This prevents an unset variable or skipped optional job from satisfying a
required context. Add the exact names produced by the repository, such as
`Build`, `Unit Tests`, `CodeQL`, `Dependency Review`, `SonarQube Quality Gate`,
or an AI review context, only after activation.

GitHub may display a workflow check as `Workflow name / Job name` depending on
how the workflow is installed and invoked. After the first successful run,
inspect the actual check-run names and update the ruleset contexts before
turning the ruleset active.

The default ruleset requires a pull request and resolved review threads, but
does not require an approving reviewer. This supports a single-developer
repository without creating a bypass. Teams can raise
`required_approving_review_count` to `1` or more, and enable
`require_last_push_approval` or
`require_extra_approval_for_unattributed_changes`, as their staffing and risk
require. It does not
enable CODEOWNER approval because CODEOWNERS is repository-specific. A
consuming repository can set `require_code_owner_review` to `true` after adding
and validating its own `.github/CODEOWNERS` file.

The ruleset blocks direct updates, force pushes, and branch deletion for the
default branch. The shared default has no bypass actors, so normal development
must use a pull request, including in a single-developer repository. If an
organization later approves emergency exceptions, configure them narrowly and
audit every use; do not place organization-specific actor IDs in this shared
template.

The JSON cannot configure repository-specific CODEOWNERS files, enable GitHub
secret scanning, choose external scanner credentials, or guarantee that a
workflow will produce a particular check context. Install and run the
workflows first, then update the required-status-check contexts to match the
actual GitHub check names.

Use the smallest useful protection that matches the repository’s risk. Add a
required check only after the check exists, has passed consistently, and has a
stable context name. Treat third-party Actions and reusable workflows as
supply-chain dependencies, and review sensitive workflow changes through
CODEOWNERS or an equivalent ownership gate.

See the current [GitHub ruleset REST schema](https://docs.github.com/en/rest/repos/rules)
before importing if GitHub changes the export format or supported rule
parameters.
