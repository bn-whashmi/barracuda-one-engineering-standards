# Release Evidence Policy

Every production or customer-facing release should leave enough durable
evidence for another operator to understand what shipped, where it shipped,
how it was verified, and how to recover if it fails.

This is an operational record, not an additional approval ceremony. Store it in
the application repository’s documented release location, such as:

```text
docs/releases/YYYY-MM-DD-<release>.md
```

## Required evidence

Record:

1. **Release identity** — commit SHA, branch, version/tag, date/timezone, and
   operator or automation when useful.
2. **Released surfaces** — web, API, admin, mobile, worker, infrastructure,
   configuration, migrations, or backfills.
3. **Deployment target** — environment, service/platform, region or project
   when safe, and revision/build/artifact ID.
4. **Verification** — exact commands, release gates, tests, smoke checks,
   health checks, and manual checks.
5. **Configuration evidence** — safe validation of required configuration,
   migrations, feature flags, queues, storage, and integrations.
6. **Rollback path** — rollback or redeploy command, previous known-good
   revision, and migration/cache/queue recovery posture.
7. **Known gaps** — skipped checks, unavailable tooling, environment limits,
   manual follow-up, accepted risk, and owner.
8. **Operator notes** — migrations, backfills, cache invalidation, propagation,
   monitoring, transient errors, and support considerations.

Do not record credentials, secret values, sensitive secret names, private
customer data, or unsafe internal details. If a check was not run, record it as
a known gap rather than implying coverage.
