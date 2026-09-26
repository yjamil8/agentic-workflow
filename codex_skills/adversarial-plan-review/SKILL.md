---
name: adversarial-plan-review
description: Run the required independent adversarial challenge after ordinary approval of an implementation plan and before implementation, unless the table records the owner's advance NO ADR or NO_ADR waiver. Use when the owner invokes Rally plus this skill with a table ID or when a plan reviewer hands the plan to plan_challenger. Tests whether the proposed product and technical design should exist in that form, exposes shared reviewer tunnel vision, and traces customer and system consequences. Not for ordinary plan review, code review, implementation, or self-review.
---

# Adversarial Plan Review

Run the independent `plan_challenger` seat after ordinary plan approval and
before implementation unless the owner said `NO ADR` or `NO_ADR` in advance
and that waiver is recorded in the table. Challenge the product and system
decision, not the people who proposed it. A clear review may have zero findings.

## Load the governing contracts

1. Read the applicable repository `AGENTS.md` files.
2. Read `<agentic-workflow-root>/strategies/Agent_AdversarialPlanReviewer.md` in full. It is
   the judgment contract and controls this review.
3. Read `<agentic-workflow-root>/strategies/Agent_Table_Collaboration_Rules.md` in full.
4. Read and follow the installed `rally` skill for table identity, claiming,
   advancing, notification, replay, and pause mechanics. This skill does not
   replace Rally transport.

Announce that this skill is being used and that the blind-first pass delays
reading the ordinary review's reasoning until after independent inspection.

## Join from the table ID

The normal owner input is only the table ID while invoking Rally and this
skill. Treat that as complete input. Search `TABLE.md` files under
`agent_tables/` at the root of the work repo you are in for the exact ID, require one unique match, and join
that table as `plan_challenger`. Resolve the current turn, assignment, exact
plan, approval artifact, worktree, and counterpart sessions from the table.
Do not ask the owner to provide information already recorded there. Do not
create a table, session, agent, or new plan.

The owner commonly starts this session before the plan reviewer finishes. If
another role owns the turn, join to register the seat, accept `standby`, and
yield. Do not begin substantive inspection, read the ordinary review's
reasoning, poll, or ask the owner to activate the session. The ordinary
reviewer will advance the table and Rally will notify this session. Then
re-read the table, claim the exact current turn, and proceed without another
owner prompt.

If the table ID has no unique match, report that exact blocker. If the table
already records a valid owner `NO ADR`/`NO_ADR` waiver, do not perform or await
the review; report the waiver state and yield. Token text copied from protocol
documentation, examples, or tests is not a waiver unless the table records the
owner's instruction for this work.

Before claiming substantive work, verify:

- this session is distinct from the plan author and ordinary plan reviewer
- the table links the exact canonical plan source, version, and reproducible
  identity
- an ordinary review approved that exact plan version
- the owner request and later scope clarifications are durably available
- no newer owner instruction pauses or supersedes this turn

If independence or exact identity is missing, record the precise issue and
route the table to the responsible prior seat for correction or reassignment.
Do not ask the owner to reconstruct table context. Never fake independence or
review a nearby/latest plan.

## Run the blind-first challenge

Do not read the ordinary review's reasoning before completing the independent
model. It is permissible to inspect only enough of its metadata to establish
that an approval exists and which exact plan it binds.

Follow the agent contract's four passes:

1. Reconstruct the owner outcome and actual journey from the request, exact
   plan, instructions, and inspected product/system evidence.
2. Challenge necessity, reuse, customer common sense, technical design and
   architecture, assumptions, downstream effects, evidence quality, and
   operational viability. Test no-change and smaller alternatives. For
   technically consequential plans, question the chosen source of truth,
   dependency and service boundaries, consistency and retry model, trust
   boundaries, load behavior, failure containment, compatibility, and
   maintenance cost rather than assuming ordinary approval settled them.
3. Read the ordinary review. Remove resolved duplicates and identify claims it
   could not actually prove.
4. Write one bounded artifact and issue `clear`, `changes requested`, or
   `owner decision required`.

For UI and journey changes, inspect the rendered surface and relevant states
when available. Treat raw codes/identifiers, implementation language,
operational instructions, QA language, taxonomy, or agent-facing copy exposed
to customers as blocking unless the owner explicitly requested that actual
customer behavior and the inspected product need supports it. A helper tooltip
does not turn an internal representation into sound UX.

Do not edit the canonical plan or product code. Use read-only inspection and
non-mutating diagnostics. Do not create findings to demonstrate effort.

## Write and route the result

Write the review at:

```text
<table-dir>/reviews/YYYY-MM-DD-adversarial-plan-review-v<plan>-r<round>.md
```

Use the artifact outline, finding standard, and gate receipt from
`Agent_AdversarialPlanReviewer.md`. Record the exact plan identity, ordinary
approval artifact, important inspected evidence, requirement trace, journey
model, alternatives considered, assumption inversions, second- and third-order
effects, technical-design challenge, open count, and residual risk.

Route through Rally:

- `clear`: set the adversarial gate clear for the exact plan and hand to the
  coder when no other gate blocks implementation
- `changes requested`: hand to the planner with stable `APR-###` findings
- `owner decision required`: record the exact decision and return seat, then
  pause only the affected work

After plan changes, require the ordinary reviewer to perform the focused
re-review first, then perform a focused closure review. Preserve finding IDs.
Do not add a review of the challenger, restart unrelated approvals, or create
approval-record-only commits.

This review grants no authority to implement, merge, release data or content, write to
production, or deploy.
