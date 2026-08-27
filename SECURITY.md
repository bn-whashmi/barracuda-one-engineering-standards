# Security Policy

## Reporting A Vulnerability

Do not open a public issue for suspected credential exposure, private data
leakage, or other sensitive vulnerabilities.

Use [GitHub private vulnerability reporting](https://github.com/ravisingh11/engineering-standards/security/advisories/new)
to report a suspected vulnerability. If that channel is unavailable, contact
the maintainer through the private contact listed on the GitHub profile. Do not
include credentials, customer data, or exploit details in a public issue.

## Sensitive Data

This repository should not contain:

- real credentials, tokens, API keys, private keys, or session artifacts
- private customer data or production payloads
- private domains, private repository inventories, or internal rollout logs
- screenshots or logs containing sensitive operational details

If sensitive data is committed, rotate the affected credential or invalidate the
affected artifact before removing it from the repository.
