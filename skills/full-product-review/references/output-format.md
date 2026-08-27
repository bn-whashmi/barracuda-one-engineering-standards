# Output Format

Create a dated review folder under `docs/reviews/` unless the user requests a different location.

Default folder name:

`docs/reviews/full-product-review-YYYY-MM-DD/`

## Required Files

### `00-index.md`

Use as the entry point for the review pack.

Required sections:

- title with date
- scope
- artifacts list
- evidence sources used

### `10-executive-summary.md`

Keep this short and decision-oriented.

Required sections:

- findings summary block
- top strengths
- open P0/P1 risks
- structural issues to revisit
- underlying technical issues
- near-term recommendation
- major-work gate

### `20-scorecard.md`

One section per axis:

- Product
- Reliability
- Security/Tenant
- Delivery
- Cost

For each axis include:

- score out of 5
- what is working
- what needs improvement

### `30-findings-ledger.md`

Use a single table with:

| ID | Theme | Priority | Status | Confidence | Surface | Evidence | Impact | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- `Confidence` should be `High`, `Medium`, or `Low`
- `Surface` should name the subsystem, area, or path concisely
- `Evidence` should reference current repo artifacts, not vague impressions
- `Next action` should be the smallest credible next move

### `40-structural-issues.md`

Required sections:

- preserve as-is
- revisit now
- defer unless trigger fires
- evidence gaps or open questions

Capture root causes, trust-boundary problems, architectural coupling, or operational assumptions here. Keep rewrite discussions gated by evidence.

### `50-priority-plan.md`

Use a staged plan:

- `0-30 Days`
- `31-60 Days`
- `61-90 Days`

Each item should include:

- concrete action
- expected outcome or KPI
- notes on dependencies when relevant

## Findings Summary Block

Use this exact shape in both `10-executive-summary.md` and the final user response:

```text
Findings summary (from <review-folder>):
Overall posture: Product <x>/5, Reliability <x>/5, Security/Tenant <x>/5, Delivery <x>/5, Cost <x>/5.
Resolved: <ids or none>.
Partially resolved: <ids or none>.
Open P0/P1 risks: <comma-separated IDs or themes>.
Working well: <one sentence>.
Structural issues to revisit: <one sentence>.
Underlying technical issues: <one sentence>.
Recommended sequence: <one sentence>.
Major re-architecture: <not recommended now | recommended> because <brief reason or gate>.
```

If there are no resolved or partially resolved items worth calling out, use `none`.
