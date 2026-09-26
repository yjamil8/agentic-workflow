# <Outcome-shaped title, for example "Merged accounts keep their in-progress work">

- Plan version: v1
- Updated: YYYY-MM-DD
- Status: <draft | in plan review | approved for vN | changes requested (PR-001, PR-002)>
- Responds to: <link to the review that triggered this version, or "initial plan">
- Agent Table: <link to TABLE.md> (table ID <uuid>)
- Source: implementation_plans/MMDDYY/<slug>-plan-YYYYMMDD.md
- Inspected source: <repo>@<40-character SHA> (note any unrelated local edits)

## Revision history

- `v1`, YYYY-MM-DD: Initial plan.

## Outcome

<Two or three sentences stating the decision in plain language, as the user
or operator will experience it. Then foreclose the most likely misreading.>

Non-goals: <what this deliberately does not change>.

## Current behavior and evidence

| Surface | Inspected behavior (file + symbol, line where precise) | Consequence |
|---|---|---|
| <component or endpoint> | `<path/to/file.ext>` `<Symbol>` (`:123`) does X | <what goes wrong or what must be preserved> |

Completeness: <the exact search you ran to find every call site, branch,
writer, and allowlist entry, for example `rg -n "SymbolName" src/`, and the
count it returned>.

## Inventory and compatibility boundary

### Existing data

<What persisted data is affected. Dated counts from a read-only query, and
what those counts do and do not prove.>

### Active clients and writers

- <Every writer and reader of the changed contract, including older cached
  clients or deployed versions still sending the old shape.>

### Reuse decision

Reuse <existing mechanism>; it already provides <needed property>. Do not add
<table, service, endpoint, migration, framework> for this change.

## Scope

<Each requirement and its basis: an owner instruction, an existing
invariant, or the inventory above.>

### Out of scope

- <Explicitly unchanged behavior, surfaces, and data.>

## Proposed changes

### 1. <Contract or surface>

<What changes and why the smallest existing mechanism is not enough, if new
machinery is proposed.>

## Feature flags and configuration

<Flag name, compile-time or runtime, default per environment, every wiring
surface that must change, and confirmation that local development enables it.
Write "None" if not applicable.>

## UI presentation, exact approved scope

<Omit only if nothing user-visible changes.>

| State | Exact copy | Interaction |
|---|---|---|
| <state> | "<exact string>" | <what happens> |

Reused components and styles: <names>. Breakpoints: <behavior per width>.
Accessibility: <focus, announcements, touch targets>. Screenshot gate:
<before/after states and viewports to capture>.

## Milestones

### Milestone 1: <User-visible journey that works end to end>

<Scope across every affected layer for this journey.>

Acceptance:

- <Concrete scenario including edge cases: concurrent, expired, wrong owner,
  stale cache, retry.>
- New regression tests fail on the base commit before the fix.

### Milestone 2: <Next journey>

## Verification

```bash
<exact commands to run, and the result that counts as passing>
```

## Rollback

1. Measure the blast radius first (read-only): <query or command and today's
   dated result>.
2. Ordered steps: <commands, in one transaction where data is involved>.
3. Kept and lost: <what rollback intentionally preserves, and accepted
   collateral>.

Invariant: <what must remain true after rollback>.

## Risks and how not to misread results

- <Risk, and what observed signal would or would not indicate a problem.>

## Release, effort, and authority

- Effort: <rough estimate, broken down if more than a day>.
- Stopping rule: <conditions under which work pauses and returns to the owner
  with smaller alternatives>.
- Authority: implementation approval is not merge or production approval.
  <Name each step that needs separate explicit owner approval.>

## Owner decisions required

1. D1: <exact decision>. Options: <A, consequence; B, consequence>. Default if
   unanswered: <A>. Resumes: <seat>. Recommendation: <A, because ...>

## Review request

<What is new in this version for the reviewer to assess, what is retained from
a prior approval, and known limits of the evidence.>
