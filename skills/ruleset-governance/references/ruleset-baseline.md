# Ruleset Baseline

GitHub rulesets can control selected branches and tags. Available rule categories include restricting creations, updates, and deletions; requiring linear history; requiring deployments; requiring signed commits; requiring pull requests; requiring status checks; blocking force pushes; requiring code scanning or code quality results; and restricting file paths, extensions, path length, and file size.

Start with the smallest useful protection:

- Protect `main` from force pushes and deletion.
- Add required checks after the check exists and has passed consistently.
- Require pull requests for all default-branch changes, including solo-developer
  repositories.
- Use zero approving reviews for a solo-developer baseline; raise the count for
  teams or higher-risk repositories.
- Do not configure a standing bypass. Emergency exceptions must be narrow,
  auditable, and documented.
- Use push rules only for high-risk patterns such as secrets, oversized files, or prohibited paths.

Source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
