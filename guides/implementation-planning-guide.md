# Implementation Planning Guide

How to write an implementation plan that survives independent review in one
or two rounds. Start from [implementation-plan-template.md](implementation-plan-template.md);
this guide explains what each part is for and what reviewers actually block on.

## Where this comes from

Derived from a production multi-agent workflow: the structure of 15 plans that
independent reviewers approved (five of them in round 1), the first-round
findings of 15 reviews across 12 workstreams (7 of which needed three or more
rounds), and pattern counts over 290 recent plans. It is not a full read of
every plan ever written. The conventions matured over time; older plans in
the source corpus often lack them.

## Before you submit: what reviewers block on

These are the first-round findings, ranked by how often they occurred. Check
your plan against each one before handing it to a reviewer.

1. **Incomplete inventory or a wrong premise about current code** (10 findings
   in 6 of 15 reviews). The plan named two of four call sites, missed a branch,
   misread a type, or described a state the code cannot reach. Fix: enumerate
   every call site, branch, writer, and allowlist entry; show the search you
   ran and its count; say how you know the list is complete.
2. **An unhandled user state or a path that strands someone** (6). A user
   partway through a flow, on a cooldown, holding an old link, or on a journey
   the change silently breaks. Fix: walk every state a real user can be in
   before, during, and after the change.
3. **Bigger machinery than needed, or the wrong operational lane** (5). A
   migration where a release step suffices, an alias layer nobody needs, an
   unrequested change riding along. Fix: justify every new mechanism against
   the smallest existing one, inline.
4. **Untraced absolute claims, or copy not true for every user** (4). "Never",
   "always", "cannot", "no longer" without the code that enforces it. Fix: cite
   the enforcing code or soften the claim to what is true.
5. **UI design or copy left to the coder, or claimed unchanged when it is
   not** (3). Fix: exact copy and states in the plan (see UI section below).
6. **A guardrail that is claimed but not enforced by construction** (3). "Caps
   at N" with nothing capping it. Fix: name the code, constraint, or config
   that enforces it.
7. **Undefined measurement or unmeasured assumptions** (3). Events that do not
   exist, a sample size that contradicts the plan's own evidence, an assumed
   rate nobody measured. Fix: name the exact event or query and measure first.
8. **No executable verification for a claim** (2), especially on money or
   data paths. Fix: exact commands and the observable result that counts as
   proof.

The single strongest lesson: most first-round blocks come from inventory that
was not exhaustive. Time spent proving completeness is the cheapest review
time you will spend.

## File naming and lifecycle

- One plan file per workstream:
  `implementation_plans/MMDDYY/<slug>-plan-YYYYMMDD.md` in the work repo.
- Update it in place. Never create `plan-v2.md`; bump `Plan version` and add a
  revision-history entry instead.
- Record the exact commit containing each submitted version so a review stays
  bound to what it read.

## The sections, and what each is for

### Header

A bullet list at the top (the plan viewer renders it as metadata chips):
version, updated date, status, the review this version responds to, the Agent
Table link and ID, and the source path. Recommended for anything touching
shared code: the inspected source commit per repo, noting unrelated local
edits. The header answers "is this the version I approved?" without a reread.

### Revision history

One line per version: number, date, what changed, and the finding ID or owner
instruction that triggered it. It is a decision log, not a changelog; "various
fixes" tells a reviewer nothing. When a reviewer approves with small
corrections, a short "Corrections that override the text below" block at the
top (versioned as, say, v1.1) is an accepted alternative to a full revision.

### Outcome

Two or three sentences stating the decision as the user or operator will
experience it, followed by the most likely misreading and why it is wrong, and
an explicit non-goal. Plans that open with a task list instead of an outcome
invite scope disputes later.

### Current behavior and evidence

Trace every claim about how the system behaves today to a file and symbol,
with a line number where precision matters. A table is useful for several
surfaces but not required. What is required is that a reviewer can verify
each claim in under a minute, and that you state how you established
completeness (finding 1 above).

### Inventory and compatibility boundary

Three short parts that together prevent findings 1 and 2:

- **Existing data.** What persisted data is affected, with dated counts from a
  read-only query, and what the evidence rules out as well as what it shows.
  Partial telemetry showing abandonment is not proof of an error; say so.
- **Active clients and writers.** Every reader and writer of the changed
  contract, including older cached clients or deployed versions that will keep
  sending the old shape for a while.
- **Reuse decision.** The existing mechanism you are reusing, what it already
  provides, and an explicit list of what you will not add (table, service,
  endpoint, migration, framework).

Example, generalized from an approved plan:

```text
Existing data: the affected rows are append-only event records. No user,
order, or entitlement record needs reconstruction or backfill; historical rows
keep their original meaning.
Active clients and writers: the web client is the only writer of this
contract, through one ingestion endpoint. Older cached client bundles will
keep emitting the current subset, so the additive change must accept both.
Reuse decision: reuse the existing event contract; do not add a table,
service, endpoint, migration, or general framework. It already carries the
needed identifiers.
```

### Scope and out of scope

Each requirement with its basis: an owner instruction, an existing invariant,
or the inventory. Then an explicit **Out of scope** list of behavior and
surfaces that do not change. Most approved small plans have one; it is the
cheapest defense against both scope creep and "you forgot X" findings.

### Proposed changes

Numbered per contract or surface. Wherever you introduce a new mechanism, say
in the same place why the smallest existing one cannot do the job. Name what
the fix does not introduce as well as what it does.

### Feature flags and configuration

If behavior is gated, name each flag, whether it is compile-time or runtime,
its default per environment, every wiring surface that must change, and
confirm local development enables it. Production enablement is often a
separate owner decision; say so explicitly.

### UI presentation (when anything user-visible changes)

Reviewers blocked every sampled plan that left this to the coder. The heading
name varies; the content does not:

- exact copy in a table: state, exact string, interaction
- the existing components and styles being reused
- behavior at each breakpoint
- accessibility: focus, announcements, touch targets
- a screenshot gate naming the before and after states and viewports

### Milestones and acceptance

For work that spans several surfaces or users, organize milestones around
journeys that can be demonstrated on their own ("Merged accounts keep their
in-progress work"), each spanning every layer it needs, rather than around
layers ("backend", "frontend", "tests"). For a small single-surface change,
ordered steps are fine; approved plans use both.

Acceptance criteria are concrete scenarios, including the awkward ones:

> An account with both a completed and an active attempt on the same item:
> the first merge and a later separate re-entry both resume the same active
> attempt, not a new one.

Not "add integration tests". Also require that each new regression test fails
on the base commit before the fix; a test that passes before the fix proves
nothing.

### Verification

Exact commands and the observable result that counts as passing, for example
"a request to endpoint X is observed with field Y", plus any dated post-deploy
read-only check. On money and data paths, verification must exercise the real
path, not a mock of it.

### Rollback

Three parts, in this order:

1. **Measure the blast radius first** with a read-only query and today's
   dated result, so whoever runs the rollback sees the number before acting.
2. **Ordered steps**, in one transaction where data is involved.
3. **What is kept and what is lost**, including accepted collateral.

Then state the invariant rollback must preserve. Example, generalized from an
approved plan:

```text
Measure first: count the parent batches that contain generated records and
the unrelated records inside them (today: 1 batch, 0 unrelated records).
Then, in one transaction: delete the parent batches that contain generated
records (children cascade), then delete the remaining generated records.
Records a user later promoted by hand are intentionally kept. Any other
in-progress record inside a deleted batch is lost; that is acceptable for a
rollback and is stated here.
```

### Risks and misreadings

Name the risks, and also the signals that will look like good or bad news but
are not. For example: "Sign-ups rise after the fix because the count was
previously under-reported; do not read it as a campaign improvement."

### Release, effort, and authority

A rough effort estimate (broken down when over a day), a stopping rule ("if X
or Y turns out to be true, stop that work and return to the owner with smaller
alternatives"), and which steps need separate explicit owner approval.
Implementation approval is never merge or production approval.

### Owner decisions required

Give each decision an ID and state the exact choice, the options with their
consequences, the default if the owner does not answer, the seat that resumes,
and your recommendation. The plan viewer renders this section as decision
cards when each item ends with `Recommendation: ...`.

### Review request

What is new in this version, what is retained from a prior approval, and the
known limits of your evidence. For later rounds, a disposition of each prior
finding by ID. When earlier versions were withdrawn for real mistakes, a short
"do not reintroduce" list keeps the implementer from repeating them.

## Anti-patterns

1. **No provenance.** No version, no inspected commit, no link to the review it
   answers. Nobody can bind an approval to it.
2. **Spec voice instead of decision voice.** "Add a workflow where an operator
   can..." describes a feature, not a traced outcome with a reason.
3. **No acceptance criteria or rollback.** Target architecture without a way
   to know it is done or to undo it.
4. **Uncited current-state claims.** "The existing flow already supports X"
   with nothing a reviewer can check, which is often wrong when checked.
5. **Layer-shaped milestones for a cross-layer journey.** When one user
   journey spans several layers and no milestone can be demonstrated on its
   own, the plan was not organized around the outcome.

## Calibrating length

The best plans are dense with evidence, not broad in scope. A tightly scoped
plan with exhaustive edge cases can be short. A plan can also grow long across
many incident-driven revisions without sprawling, provided each addition is
small, justified, and tied to a named trigger. Do not pad a plan to look
thorough, and do not compress it past the point where its claims are
checkable.

## See also

- [Agent_AdversarialPlanReviewer.md](../strategies/Agent_AdversarialPlanReviewer.md):
  the challenge lenses a plan must survive after ordinary approval.
- [Agent_Table_Collaboration_Rules.md](../strategies/Agent_Table_Collaboration_Rules.md):
  versioning, immutable dated reviews, and the UI presentation gate.
- `scripts/serve_implementation_plans.py`: render a plan while you write or
  review it.
