# Organization Semgrep Candidates

These are candidate organization-wide rules, not complete executable Semgrep
rules. Application repositories differ in tenancy models, query builders,
transport stacks, and administrative routing. A pattern that is not validated
against those contexts creates false confidence.

Candidate rules:

- Require the approved account boundary key (on Nexus: `bcc_account_id` /
  `BccAccountId`) before customer account data access; authorization
  follows the BCC account hierarchy.
- Reject SQL construction from user-controlled strings; prefer parameterized
  queries or approved query builders.
- Reject logging of authentication tokens, session credentials, and equivalent
  auth artifacts.
- Reject disabling TLS or certificate validation outside an explicitly approved
  test fixture.
- Reject unauthenticated administrative endpoints.

Before making a rule blocking, define its approved exceptions, test it against
representative repositories, measure false positives, and assign an owner.
Then add it to the consuming repository's configured Semgrep command or to an
organization-managed Semgrep integration.
