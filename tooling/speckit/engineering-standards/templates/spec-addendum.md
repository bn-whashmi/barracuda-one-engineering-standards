## Engineering Standards Addendum

### Work Item Link

- **Issue or Tracker**: [Link or "Not required for this change"]
- **Reason Spec Kit Is Being Used**: [new feature / cross-client work / unclear requirements / risky refactor / other]

### Standards Checks

- [ ] No secrets, tokens, customer data, private logs, or sensitive operational
  details are included.
- [ ] User-facing behavior is described without implementation details.
- [ ] Cross-client or multi-surface parity is identified when applicable.
- [ ] Security, privacy, and authorization expectations are explicit when the
  feature touches sensitive data or privileged actions.
- [ ] Success criteria are measurable and can be verified through the repo's
  chosen validation model.

### Release Evidence Impact

- **Production-facing release?** [Yes/No]
- **Evidence location if yes**: [docs/releases/... or issue comment]
- **Rollback expectation**: [short description or "Not applicable"]
