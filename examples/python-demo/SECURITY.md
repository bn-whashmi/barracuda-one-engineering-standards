# Security

This demo has no network, authentication, tenant-data, or persistence layer.

- Do not add secrets or tokens to source, tests, logs, or reports.
- Validate inputs at new boundaries.
- Do not construct SQL from user input or disable TLS validation if a future
  integration adds those boundaries.
- Security-sensitive changes require a focused security review.
