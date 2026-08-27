## Engineering Standards Gates

### Validation Gate

- [ ] The repo's validation model is identified.
- [ ] Planned checks are runnable in that model.
- [ ] Skipped checks have a concrete reason and follow-up owner.

### Security And Privacy Gate

- [ ] New or changed trust boundaries are documented.
- [ ] Sensitive data handling is explicit.
- [ ] User-facing errors and operator diagnostics follow the error-handling
  standard.
- [ ] Logs and artifacts avoid secrets, tokens, private customer data, and
  unnecessary PII.

### Parity And Contract Gate

- [ ] Required clients or deployable surfaces are listed.
- [ ] API, SDK, schema, fixture, or serialization contracts are identified.
- [ ] Contract drift checks are included when interfaces change.

### Release Gate

- [ ] Deployment target and release path are known for production-facing work.
- [ ] Rollback path is documented.
- [ ] Release evidence location is identified before implementation begins.
