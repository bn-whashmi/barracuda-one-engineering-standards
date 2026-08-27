# GitHub Actions Security Policy

Apply this baseline to every shared or repository-local GitHub Actions
workflow.

- Grant `GITHUB_TOKEN` the minimum permissions needed; default to
  `contents: read`.
- Never store sensitive values as plaintext in workflow files.
- Register and mask transformed secrets, not only their original values.
- Pass untrusted GitHub context through environment variables or purpose-built
  actions instead of interpolating it directly into shell scripts.
- Treat third-party Actions and reusable workflows as supply-chain
  dependencies.
- Pin sensitive third-party Actions to full commit SHAs when immutability
  matters; document readable-tag exceptions.
- Prefer OIDC over long-lived cloud credentials where supported.
- Use CODEOWNERS or equivalent review gates for workflow changes when a
  repository has multiple maintainers.
- Treat `pull_request_target`, deployment secrets, and write tokens as
  high-risk until their trust boundary is documented.

The workflow templates in `workflows/` pin their third-party Actions to
immutable commit SHAs and provide conservative permissions and configuration
interfaces. Consuming repositories remain responsible for keeping those pins
current after review, pinning any additional actions they add, and configuring
their own secrets, runners, and external tools.
