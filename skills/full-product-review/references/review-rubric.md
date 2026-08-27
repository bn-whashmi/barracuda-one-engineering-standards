# Review Rubric

Use this rubric to keep full product reviews consistent across repositories and dates.

## Scoring Scale

Score each axis from `1` to `5`.

| Axis | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Product | Core value is unclear, broken, or hard to trust. | Core workflows are usable, but friction or inconsistency is material. | Value is clear, important flows are polished, and tradeoffs are deliberate. |
| Reliability | Recurring failures, weak safeguards, poor recovery, or missing tests. | Most flows work, but there are known hot spots or confidence gaps. | Stable flows, strong checks, and good fault isolation. |
| Security/Tenant | Trust boundaries are weak, privileged paths are unsafe, or tenant isolation is fragile. | Important basics are in place, but meaningful gaps remain. | Trust boundaries are clear, enforced, and regression-resistant. |
| Delivery | Releases are manual, risky, slow, or difficult to verify. | Some automation exists, but consistency or rollback discipline is uneven. | Delivery is predictable, observable, and easy to validate. |
| Cost | Cost drivers are opaque or routinely surprising. | Major cost drivers are mostly known, but hotspots or drift remain. | Costs are visible, intentional, and shaped by technical controls. |

## Finding Priorities

- `P0`: release blocker, tenant/security exposure, active data integrity risk, or repeated core-flow failure
- `P1`: near-term reliability or structural risk likely to cause incidents, support load, or delivery drag
- `P2`: important but not immediately blocking; should be sequenced after hardening
- `P3`: opportunistic or deferred work

## Finding Statuses

- `Open`: confirmed and not yet fixed
- `Partially Resolved`: some mitigating change exists, but the risk is not fully removed
- `Resolved`: evidence shows the issue is fixed at current HEAD
- `Needs Re-check`: prior report exists but current evidence is incomplete or stale
- `Deferred`: intentionally postponed pending a later decision or dependency
- `Obsolete`: no longer relevant because the surface was removed or the prior report was superseded

## Finding IDs

Preserve canonical IDs from prior audits or backlog items when they already exist.

When creating new IDs, use stable prefixes:

- `PROD-###` for product/UX findings
- `REL-###` for reliability findings
- `SEC-###` for security or tenant-boundary findings
- `DEL-###` for delivery, CI, release, or operational discipline findings
- `COST-###` for cost and efficiency findings
- `ARCH-###` for structural or architectural findings

If multiple notes describe the same root cause, keep one canonical ID and append evidence instead of creating duplicates.

## Decision Rules

- Favor the smallest credible next step over broad redesign.
- Recommend major re-architecture only when at least one of these is true:
  - repeated Sev-1 or Sev-2 incidents in core flows
  - recurring manual operational intervention for the same structural defect
  - support burden is materially crowding out planned product work
  - unresolved P0 structural risk remains after the committed hardening window
- If the threshold is not met, recommend incremental hardening plus staged structural follow-through.
