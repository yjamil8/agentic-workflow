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
8. **No executable verification for a claim** (2), especially on data,
   content, or third-party paths. Fix: exact commands and the observable result that counts as
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

Every section is either **always** included or included **when applicable**.
Delete a when-applicable section that does not apply; never keep it as "N/A".
Replace every `<placeholder>` or delete its line. The seven always sections
match the smallest plan in the source survey that reviewers approved in round
1, so a small plan really can be that short.

| Section | Include | Trigger for optional sections |
|---|---|---|
| Header | Always | Optional fields as marked in the template |
| Revision history | Always | |
| Outcome | Always | |
| Owner decisions required | When applicable | A choice existing authority cannot resolve |
| Current behavior and evidence | Always | |
| Inventory and compatibility boundary | When applicable | Persisted data, an API or event contract, or its clients or writers change |
| Requirements and out of scope | Always | |
| Proposed changes | Always | |
| Security, privacy, and compliance | When applicable | Authentication, authorization, secrets, personal data, or regulated data |
| Feature flags and configuration | When applicable | Behavior is gated or configuration changes |
| UI presentation, exact approved scope | When applicable, then mandatory | Any user-visible change |
| Milestones | When applicable | Two or more journeys that can each be demonstrated alone |
| Acceptance and verification | Always | |
| Rollback | When applicable | Data, a content release, config, or a third-party service a code revert does not undo |
| Risks and how not to misread results | Always | |
| Delivery and authority | When applicable | Deploy, content release, third-party change, hotfix, multi-repo, or separate approval |
| Required updates | When applicable | A documentation or process obligation your team's rules attach to the change |
| Review request | When applicable | v2 onward, or any re-review |

### Header

A bullet list directly under the title; the plan viewer renders it as
metadata chips. Always: version, updated date, status, Agent Table, plan
viewer URL, source path, repos, and effort. When applicable: the review this
version responds to, the inspected source commit per repo, the review-gate
state (including any owner `NO_ADR` waiver, copied from `TABLE.md`, which
stays authoritative), and the tracking ticket. The header answers "is this the
version I approved?" without a reread.

### Revision history

One line per version: number, date, what changed, and the finding ID or owner
instruction that caused it. "Various fixes" tells a reviewer nothing. When a
reviewer approves with small corrections, a short "Corrections that override
the text below" block at the top (as v1.1) is an accepted alternative.

### Outcome

Two or three sentences stating the decision as the user or operator will
experience it, followed by the most likely misreading and why it is wrong.
Plans that open with a task list invite scope disputes later. Non-goals go in
the out-of-scope list, not here.

### Owner decisions required

Placed directly after the outcome so a blocking decision is seen first. Give
each an ID (D1, D2), the exact choice, whether it blocks and what, the options
and consequences, the default if unanswered, the resuming seat, and a trailing
`Recommendation: ...` (the viewer renders these as decision cards).

### Current behavior and evidence

Why the work is needed, traced to code and data. Each claim about today's
behavior cites a file and symbol, with a line number where precision matters.
A table helps for several surfaces but is not required. State how you
established completeness (finding 1 above).

### Inventory and compatibility boundary

Three parts that together prevent findings 1 and 2:

- **Existing data**: what persisted data is affected, with dated counts from
  the QA database (read-only, labeled as QA), and what the evidence rules out
  as well as what it shows. Production is not readable, so say what QA cannot
  tell you and design for that unknown, or name who can check it (see
  `AGENTS.md` "Environments And Data Access").
- **Active clients and writers**: every reader and writer of the changed
  contract, including cached clients and deployed versions that will keep
  sending the old shape.
- **Reuse decision**: the existing mechanism reused, what it already provides,
  and an explicit list of what you will not add.

Example, generalized from an approved plan:

```text
Existing data: the affected rows are append-only event records. No user or
account record needs reconstruction or backfill; historical rows
keep their original meaning.
Active clients and writers: the web client is the only writer of this
contract, through one ingestion endpoint. Older cached client bundles will
keep emitting the current subset, so the additive change must accept both.
Reuse decision: reuse the existing event contract; do not add a table,
service, endpoint, migration, or general framework. It already carries the
needed identifiers.
```

### Requirements and out of scope

What must be true when the work is done, each with its basis (owner
instruction, existing invariant, or inventory), then an explicit out-of-scope
list including non-goals. Requirements say what; proposed changes say how.

### Proposed changes

Numbered per contract or surface. Wherever a new mechanism appears, say in the
same place why the smallest existing one cannot do the job, and name what the
change deliberately does not add.

### Security, privacy, and compliance

The trust boundaries and authorization checks affected, what personal or
regulated data is read, stored, logged, or sent and for how long, where
secrets live, and which reviews your organization requires. A plan that
touches these and says nothing about them should not pass review.

### Feature flags and configuration

Each flag, compile-time or runtime, default per environment, and every wiring
surface in `AGENTS.md` "Feature Flag Wiring Discipline". Confirm local
development enables it. Production enablement is often a separate owner
decision; say so.

### UI presentation, exact approved scope

Mandatory for any user-visible change under the
[UI presentation approval gate](../strategies/Agent_Table_Collaboration_Rules.md#ui-presentation-approval-gate).
Reviewers blocked every sampled plan that left this to the coder. Include an
exact copy table, reused components and styles, breakpoints, accessibility,
icon alignment, and a screenshot gate naming before and after states and
viewports.

### Milestones

For work spanning several independently demonstrable journeys, name each
milestone after the journey (`### Milestone 1: <journey>`, rendered as a
milestone card), spanning every layer it needs, with its own acceptance
scenarios. For a single-journey change, skip this section; ordered steps in
Proposed changes are fine. Layer-shaped milestones ("backend", "frontend",
"tests") for a cross-layer journey are an anti-pattern.

### Acceptance and verification

Concrete scenarios, including the awkward ones:

> An account with both a completed and an active attempt on the same item:
> the first merge and a later separate re-entry both resume the same active
> attempt, not a new one.

Not "add integration tests". Add the exact commands and observable results
that count as passing, and how the change will be confirmed after deploy
through behavior or telemetry you can access. Each new regression test must
fail on the base commit before the fix. Name the local database and Azure
Storage (Azurite) setup the verification needs; tests never touch QA or any
shared environment. For third-party services, use a sandbox or test account
where one exists, and make any test double match the real responses and
errors.

### Rollback

When a code revert is not enough: measure the blast radius first (in QA,
plus the exact read-only query for someone with production access), then give
ordered steps, then say what is kept and lost, then the invariant rollback
must preserve. A pure code change needs no section. Example, generalized from
an approved plan:

```text
Measure first: count the parent batches that contain generated records and
the unrelated records inside them (in QA today: 1 batch, 0 unrelated records;
the same query is run against production by someone with access before rollback).
Then, in one transaction: delete the parent batches that contain generated
records (children cascade), then delete the remaining generated records.
Records a user later promoted by hand are intentionally kept. Any other
in-progress record inside a deleted batch is lost; that is acceptable for a
rollback and is stated here.
```

### Risks and how not to misread results

Name the risks, how you would detect each in production (metric, log, or
alert), and the signals that will look like good or bad news but are not. For
example: "Sign-ups rise after the fix because the count was previously
under-reported; do not read it as a campaign improvement."

### Delivery and authority

The branch and lineage (for a production hotfix, start from the exact commit
currently deployed, not from `main`), the deploy order, any content release
through the GitHub Actions release workflow (separate from the code deploy), any change-management record your
organization requires, each step needing separate explicit approval, and a
stopping rule for multi-day work. Plan approval is never merge or production
approval.

### Required updates

The documentation and process obligations your team attaches to certain
changes: the tracking ticket, runbooks and on-call docs, user-facing docs or
release notes, API documentation, dashboards and alerts, and the team's agent
instructions when the workflow itself changes. List only the ones this change
triggers, so the reviewer can check them off.

### Review request

From v2 onward: what is new in this version, what is retained from a prior
approval, a disposition of each prior finding by ID, and the limits of your
evidence. If earlier versions were withdrawn for real mistakes, add a short
"do not reintroduce" list.

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
