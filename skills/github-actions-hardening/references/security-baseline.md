# GitHub Actions Security Baseline

Use GitHub's current security guidance as the baseline:

- Grant `GITHUB_TOKEN` the minimum permissions needed; default to read-only contents.
- Do not store sensitive values as plaintext in workflow files.
- Register and mask transformed secrets, not only the original secret.
- Avoid script injection by passing untrusted GitHub context through environment variables or purpose-built actions rather than interpolating directly into shell scripts.
- Treat third-party actions and reusable workflows as supply-chain dependencies.
- Pin sensitive third-party actions to full commit SHAs when immutability matters.
- Prefer OIDC over long-lived cloud credentials where supported.
- Use CODEOWNERS or equivalent review gates for workflow changes when a repo has multiple maintainers.

Source: https://docs.github.com/en/actions/reference/security/secure-use
