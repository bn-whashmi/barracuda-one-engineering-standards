# Architecture

This repository has two jobs:

1. Define the engineering policy and evidence contract.
2. Give application repositories reusable building blocks for enforcing that
   policy.

It does not become the application repository's architecture document. The
application repository remains responsible for its own code, commands,
services, credentials, ownership, and ground truth.

## Status legend

The diagrams use the following meaning:

| Visual | Meaning |
| --- | --- |
| **GREEN ✅** | GitHub-native control that can satisfy policy through GitHub settings, rulesets, or Actions. |
| **ORANGE 🟠** | Control that needs a third-party service or organization-owned external adapter. |
| **GRAY ⚪** | Repository-specific configuration or a shared template; no external vendor is implied. |
| Green arrow | Active path with a real producer and validation. |
| Orange dashed arrow | Path that still needs external configuration. |
| Dashed border | A repository-owned adapter or external service is required. |

The check symbols describe how a control can be activated. They do not mean
that every consuming application has already enabled it. See
[control-status.md](control-status.md) for the exact boundary.

## Canonical repository layout

The five public areas are the product surface. Supporting implementation is
kept separate so application teams can consume the standards without needing
to understand the evaluator internals.

```text
policies/       Organization policy and control catalog
pr-review/      AI review contracts and finding conventions
workflows/      Reusable producer workflow templates
rulesets/       GitHub enforcement templates
skills/         Reusable agent capabilities

guardrails/     Policy/evidence schemas and deterministic evaluator
tooling/        Install, configure, scan, scorecard, and validation commands
docs/           Human and agent operating documentation
```

`policies/`, `pr-review/`, `workflows/`, `rulesets/`, and `skills/` are the
shared contract. `guardrails/` and `tooling/` make that contract executable.
`docs/` explains how to consume it. None of these folders own an application's
architecture, deployment model, or repository ground truth.

## The whole system

```mermaid
flowchart LR
    engineer[Engineer + AI] --> change[Change and tests]
    change --> pr[Pull request]
    pr --> active[Shared policy and evidence contract]
    active --> evaluate[Guardrail evaluator]
    evaluate --> decision{Evidence meets policy?}
    decision -->|yes| merge[Merge when repository rules allow]
    decision -->|no| fix[Resolve blocking findings]
    fix --> change

    pr -.-> configure[Application repository configuration]
    configure -.-> checks[Build, tests, SonarQube, SAST, secrets, dependencies, Snyk, FOSSA, AI review]
    checks -.-> evidence[Revision-bound evidence]
    evidence -.-> evaluate

    classDef active fill:#dcfce7,stroke:#15803d,color:#14532d;
    classDef config fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-dasharray: 5 5;
    classDef contract fill:#f3f4f6,stroke:#6b7280,color:#111827;

    class engineer,change,pr,active,evaluate,decision,merge,fix active;
    class configure,checks,evidence config;
    linkStyle 0,1,2,3,4,5,6,7 stroke:#16a34a,stroke-width:3px;
    linkStyle 8,9,10,11 stroke:#d97706,stroke-width:3px,stroke-dasharray:5 5;
```

The solid green path is the shared repository's active control loop. The
amber dashed path is where each application repository supplies its own build
commands, test commands, scanner configuration, secrets, and AI adapter. Snyk
is an orange advisory provider on that path: teams can connect it and learn
from findings before promoting it to a required merge check.

## How policy becomes a merge decision

```mermaid
flowchart TB
    policy[Policies and control catalog]
    templates[Workflow templates]
    producer[Configured check producers]
    evidence[Evidence for the exact revision]
    evaluator[Deterministic guardrail evaluator]
    ruleset[GitHub ruleset]
    merge[Merge permitted]

    policy -->|ACTIVE| evaluator
    policy -.->|CONFIGURE| templates
    templates -.->|CONFIGURE| producer
    producer -.->|CONFIGURE| evidence
    evidence -->|ACTIVE| evaluator
    evaluator -->|ACTIVE| ruleset
    ruleset -->|ACTIVE when installed| merge

    classDef active fill:#dcfce7,stroke:#15803d,color:#14532d;
    classDef config fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-dasharray: 5 5;
    classDef contract fill:#f3f4f6,stroke:#6b7280,color:#111827;
    class policy,evidence,evaluator,ruleset,merge active;
    class templates,producer config;
    linkStyle 0,4,5,6 stroke:#16a34a,stroke-width:3px;
    linkStyle 1,2,3 stroke:#d97706,stroke-width:3px,stroke-dasharray:5 5;
```

The evaluator can only make a trustworthy decision when a check has a real
producer and the evidence identifies the revision under review. A template
without a configured producer is not a passing check.

## Where the controls run

```mermaid
flowchart LR
    subgraph shared[Shared standards repository]
        p[Policies]
        c[Control catalog]
        s[Schemas]
        e[Evaluator]
        v[Validation workflow]
        p --> c
        c --> s
        s --> e
        e --> v
    end

    subgraph app[Application repository]
        g[Ground truth]
        w[Configured workflows]
        r[Repository ruleset]
        g --> w
        w --> r
    end

    c -.->|CONFIGURE| w
    e -.->|CONFIGURE| r
    w -.->|evidence| e

    classDef active fill:#dcfce7,stroke:#15803d,color:#14532d;
    classDef config fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-dasharray: 5 5;
    class p,c,s,e,v active;
    class g,w,r config;
    linkStyle 0,1,2,3 stroke:#16a34a,stroke-width:3px;
    linkStyle 4,5,6,7,8 stroke:#d97706,stroke-width:3px,stroke-dasharray:5 5;
```

The shared repository owns reusable policy and enforcement components. The
application repository owns the facts and configuration that only it can
know.

## Control lifecycle

Every control follows the same path:

```text
Policy
  → producer
  → evidence for a revision
  → evaluator result
  → GitHub status check or ruleset requirement
```

If any step is missing, the control is documented as configurable rather than
shown as active. This prevents a workflow file or policy document from being
mistaken for enforcement.

## Related documents

- [Control status](control-status.md) — what is active, configurable, or future.
- [Control catalog](../policies/control-catalog.yaml) — machine-readable control contracts.
- [Workflow templates](../workflows/README.md) — how application repositories connect producers.
- [Ruleset notes](../rulesets/README.md) — how checks become merge protections.
- [Guardrail implementation](guardrails-implementation.md) — evidence and evaluator details.
