# Implementation Planning Guide

## Why this guide exists

This is distilled from a survey of several hundred real implementation plans
written under this toolkit's Agent Table protocol, cross-checked against what
[Agent_AdversarialPlanReviewer.md](../strategies/Agent_AdversarialPlanReviewer.md)'s
challenge lenses actually demand a plan supply. The pattern is consistent: the
plans that passed independent review cleanly, in one or two rounds, all share
a recognizable structure and a few specific habits. The plans that took many
rounds, or that a reviewer had to send back repeatedly, are missing the same
handful of things almost every time.

The formal structure below is a convention that matured over time in the
source project, not something every historical plan followed from day one.
Treat it as the target shape for a new plan, not proof that an old, thinner
plan was wrong for its moment.

## The canonical section template

A strong plan for anything non-trivial has these sections, in roughly this
order. Small, low-stakes changes can compress or drop sections that don't
apply; the point is what each section is *for*, not filling out a fixed form.

### 1. Header block

Title, `Plan version: vN`, `Updated: <date>`, `Status:` (one line naming the
exact review/authorization state), `Responds to:` (link to the review that
triggered this version, if any), the governing Agent Table link and ID, the
plan's viewer URL and repo-relative source path, and the exact inspected
source identity (commit SHAs per affected repo, with a note if the working
tree has unrelated local edits).

This is what lets a reviewer answer "is this the version I already approved,
or a new one?" without reading the whole plan again.

### 2. Revision history

One bullet per version: the version number, date, and a one-sentence summary
of what changed *and why* — which finding or owner instruction triggered it.

```markdown
## Revision history

- `v1`, 2026-09-04: Initial researched plan.
- `v2`, 2026-09-04: Addressed PR-001 (unproven current-behavior claim) and
  PR-002 (missing rollback); added feature-flag wiring for both services.
```

This is a decision log, not a changelog. A reader should be able to
reconstruct *why* the plan grew without re-reading every prior round. Avoid
"various fixes" or "addressed review feedback" — name the finding.

### 3. Decision and owner outcome

State the actual behavior or outcome in plain terms, as a product decision,
before any implementation detail. This is the outcome trace the adversarial
reviewer's first challenge lens demands, and it should be readable by someone
who has never seen the codebase.

> Example shape (paraphrased from a real plan, genericized): "Signing in
> selects the **signed-in account** as the source of truth. A second identity
> with separate progress is a possible *source for an explicit merge*, not an
> alternate account silently shown alongside it."

Notice the shape: it states the decision, then immediately forecloses the
most likely wrong reading of it. That second sentence is doing real work —
it's answering "but what about the other case?" before a reviewer has to ask.

### 4. Current behavior and evidence

A table, not prose: `Surface | Inspected behavior (file:line) | Consequence`.

Every claim about how the system currently behaves traces to an exact file
and line, never a paraphrase of what the code "probably does." This is the
single most reliable signal separating plans that passed review in one round
from ones that bounced repeatedly: a reviewer can verify a cited claim in
under a minute, but has to re-derive an uncited one from scratch, and often
finds it's wrong.

### 5. Affected inventory (when data or users are involved)

Exact counts from a real, read-only query, with the query's date and an
explicit statement of what it does and doesn't prove.

> Example shape, genericized from a real incident plan: "23 page views, four
> distinct visitors in the affected window. No newly created order, session,
> or provider-callback rows in that window." The plan then states plainly:
> "Abandonment alone does not establish an error or its root cause."

State what the evidence *rules out*, not only what it shows. Overclaiming a
root cause from partial telemetry is a common, expensive mistake; a plan that
explicitly bounds its own evidence is more trustworthy, not less.

### 6. Required behavior and boundaries

A table: `Requirement | Basis`. Each requirement traces to an owner
instruction, an existing invariant, or the affected inventory above — never
to "it would be good practice" alone. This turns the first challenge lens
(outcome and scope trace) into something a reviewer can check line by line
instead of having to infer from the narrative.

### 7. Proposed contracts and implementation

Numbered sections per surface or contract. For each new piece of machinery,
state explicitly why the smallest existing mechanism can't do the job.

> Example shape: "A new narrow read endpoint is justified because the
> existing paginated list endpoint does not expose the relation needed to
> prove ownership before the merge step; extending it would leak that
> relation to every caller of the list endpoint, not just this one."

This pre-empts the adversarial reviewer's "can an existing service already do
this?" question inline, instead of waiting for it to come back as a finding
in the next round.

### 8. UI presentation, exact approved scope (when user-visible)

Required whenever the change touches anything a user sees, per the
[UI presentation approval gate](../strategies/Agent_Table_Collaboration_Rules.md#ui-presentation-approval-gate).
It doesn't need a fixed heading name, but it needs this content:

- exact copy in a table (`State | Exact copy | Interaction`), not "reasonable
  copy" or "something like..."
- named component/style reuse — pull from what already exists; a new shared
  token or component for a one-off change is a flag, not a default
- explicit responsive breakpoints and behavior
- accessibility behavior: focus handling, live-region announcements, touch
  target sizing
- a stated screenshot gate: exactly which before/after states must be
  captured, and at what viewports

Putting exact copy in a table before implementation starts is what lets a
reviewer approve *wording*, not a vague impression, and stops the person
implementing from improvising tone.

### 9. Working milestones and acceptance

Milestones are end-to-end user journeys, not architectural layers. "Account
merge completes and stays usable" is a milestone; "backend," "frontend," and
"tests" are not — they're a waterfall wearing a milestone's name, and they
force the coder to hand off before anything is actually demonstrable.

Acceptance criteria are concrete scenarios, including edge cases, not test
categories:

> Good: "a canonical account with both a prior completed attempt and an
> active attempt on the same item: the first merge and a later, separate
> re-entry into the same flow must both resume the exact same in-progress
> attempt, not create a second one."
>
> Not this: "add integration tests for the merge flow."

The first is executable and falsifiable by a reviewer without reading the
implementation. The second isn't a criterion at all.

### 10. Release and limits

A rough effort estimate, an explicit statement of what this plan does and
does not authorize (implementation approval is not deployment approval),
and rollback stated as an **invariant**, not a script:

> Example shape: "Rollback must leave previously merged accounts under their
> canonical owner; never attempt to move them back by restoring older UI
> code." That's a constraint on what rollback must *preserve*. A list of
> commands to run is far more brittle, because the actual state of the system
> may have moved on by the time rollback is needed.

### 11. Review request and residuals

Tell the reviewer exactly what's new to assess in this round versus what's
retained from a prior approval, and name the known limits of the evidence
gathered so far. Don't make the reviewer guess which parts changed.

## Do-this best practices

1. **State what the evidence rules out, not just what it shows.** A partial
   telemetry read that shows abandonment is not proof of an error; say so
   explicitly rather than let the reader assume causation.
2. **Trace every current-behavior claim to file:line.** This is the highest-
   leverage single habit in the whole survey. It converts a review from "is
   this plausible?" to "is this cited claim actually true?" — a much faster
   and much more reliable question to answer.
3. **Justify new machinery against the smallest existing alternative,
   inline**, in the section that proposes it, not as a defensive afterthought
   if a reviewer pushes back.
4. **Give acceptance criteria as real scenarios**, including the awkward
   concurrent/expired/wrong-owner/stale-cache cases, not test categories.
5. **Make the revision history a decision log.** Name the finding ID or
   owner instruction that triggered each version bump. A plan that grew to
   seven revisions over two days of an incident stayed coherent specifically
   because each entry named its trigger in one sentence.
6. **State rollback as an invariant**, i.e. what must remain true afterward,
   not a runbook of commands that may not match the system's state by the
   time it's needed.
7. **Put UI copy in a table with exact strings**, before implementation, not
   as a placeholder to be finalized later.
8. **Name what the smallest fix does *not* introduce.** "This adds no new
   schema, index, service, or migration; do not substitute a generic
   framework for what is one narrow query fix." Explicitly ruling out
   over-engineering is as load-bearing as describing the fix itself, and it
   directly forecloses the most common reason small fixes balloon in review.

## Anti-patterns to avoid

1. **No provenance metadata.** No version number, no reviewed-commit
   identity, no link to a review artifact. A reader can't tell what was
   actually inspected, when, or bind an approval to an exact identity.
2. **Spec-document voice instead of decision voice.** "Add a new workflow
   where an operator can..." reads like a feature request, not a traced
   outcome with a stated *why*. It starves the outcome-trace and
   customer-common-sense challenge lenses of anything to check.
3. **No acceptance criteria or rollback section at all.** Describing target
   architecture without describing how to know it's done, or how to undo it
   if it's wrong, is the single most common reason a plan needs another
   round.
4. **Current-state claims with no file:line citation.** "Existing behavior
   already supports X" as a bare assertion forces the reviewer to re-derive
   the claim from scratch — and it is often wrong when checked.
5. **Waterfall-by-layer structure.** Sections named after architectural
   layers ("Service A," "Service B," "Tests") instead of user-visible
   journeys are a strong signal the plan wasn't actually organized around the
   outcome. The strongest plans consistently span all affected layers within
   one journey-shaped milestone.

## Versioning in practice

Use `Plan version: vN` from the first draft, even for a plan you expect to
approve in one round. It costs nothing when unused and is exactly what's
missing from the plans that bounced hardest in the survey. When a version
bump happens, tie it to an exact finding ID or owner instruction in the
revision history — not "various fixes."

## Length and scope calibration

The strongest plans are long in **evidence density**, not in scope. A tightly
scoped plan covering one coherent outcome across a few milestones, with
exhaustive edge-case enumeration, can be short. A plan that grows across many
revisions while tracking a real, evolving incident can be long without
sprawling, as long as each addition is small, individually justified, and
tied to a real trigger. The anti-pattern is breadth without evidence — a
short plan that skips citations and acceptance criteria — not length itself.
Don't pad a plan to look thorough; don't compress it past the point where its
claims are checkable.

## See also

- [Agent_AdversarialPlanReviewer.md](../strategies/Agent_AdversarialPlanReviewer.md) —
  the challenge lenses a plan should be able to survive.
- [Agent_Table_Collaboration_Rules.md](../strategies/Agent_Table_Collaboration_Rules.md) —
  plan versioning mechanics, the UI presentation approval gate, and immutable
  dated reviews.
- [scripts/serve_implementation_plans.py](../scripts/serve_implementation_plans.py) —
  render `implementation_plans/*.md` into a readable, linkable view while
  writing or reviewing one.
