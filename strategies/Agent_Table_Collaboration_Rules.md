# Agent Table Collaboration Rules

## Purpose

The Agent Table is a file-based collaboration protocol for agents working in
separate sessions. It allows a planner, reviewer, coder, QA agent, deployment
agent, or invited specialist to exchange complete work without the owner copying
and pasting responses between sessions.

The protocol is tool-agnostic. Codex and Claude Code sessions hold seats at the
same table, reading and writing the identical `TABLE.md` format, each running its
own helper. This document is the shared contract; anything specific to one
tool's identity source, notification transport or helper commands belongs in
that tool's own rally skill, not here.

The direct-handoff workflow is deliberately simple:

- the owner is the dealer
- each session occupies one seat at a time
- the owner assigns the initial roles and names the existing sessions
- `TABLE.md` records the current state and links to the active artifacts,
  including the required adversarial plan challenge or owner waiver
- plans, reviews, and other evidence required by the task live in linked files
- only one seat has the turn
- after finishing its turn, the agent updates the table, notifies the next
  registered session directly, and yields
- no manual dealer activation is needed unless the owner explicitly requests a
  wait or a genuine unresolved decision requires owner input

There is no autonomous orchestrator, polling loop, background daemon, or need to
share session history. Each tool supplies its own notification channel and its
own helper for create, join/resume and handoff:

- Codex: [`$rally`](../codex_skills/rally/SKILL.md)
- Claude Code: [`/rally`](../claude_skills/rally/rally.md)

Existing tables retain their canonical files and history; adopting direct
continuation does not require a format migration or create new authority to
implement, merge, or deploy.

## Core Principle

The filesystem is the communication channel. Chat messages are notifications,
not workflow state.

Every agent must be able to join the table with only:

1. the absolute path to `TABLE.md`
2. the seat assigned by the dealer
3. the repository instructions available in the workspace

An agent must not need a pasted response, a summary from another chat, or the
other agent's conversation history. If information matters to the work, it must
be written to a linked artifact.

## The Table

Each workstream gets its own table directory. The one canonical implementation
plan remains in the repository's normal `implementation_plans`
location and is linked from the table. The recommended layout is:

```text
<repo-root>/
|-- implementation_plans/
|   `-- 090426/
|       `-- example-implementation-plan-20260904.md
`-- agent_tables/
    `-- <workstream>/
        |-- TABLE.md
        |-- reviews/
        |   |-- 2026-09-04-plan-review-v1-r01.md
        |   |-- 2026-09-04-plan-review-v2-r02.md
        |   |-- 2026-09-05-code-review-r01.md
        |   `-- 2026-09-05-code-review-r02.md
        |-- qa/
        |   |-- 2026-09-05-qa-r01.md
        |   `-- 2026-09-05-qa-r02.md
        |-- deployment/
        |   `-- 2026-09-05-deploy-readiness-r01.md
        |-- consultations/
        |   `-- 2026-09-04-security-r01.md
        `-- decisions/
            `-- 2026-09-04-owner-decision-d01.md
```

The exact folders may be reduced for a small task. `TABLE.md` must remain the
single entry point regardless of layout.

Raw test output, screenshots, browser traces, generated audit output, and other
temporary evidence must follow the repository's artifact-retention rules. A
concise authored evidence record may link to local output without committing
the generated output itself.

## How The Table Operates

```text
                         AGENT TABLE -- DIRECT HANDOFF

                     +-----------------------------+
                     |        OWNER / DEALER       |
                     | assigns initial chat roles; |
                     | resolves owner choices      |
                     +--------------+--------------+
                                    |
                          "Join this table as..."
                                    |
                                    v
   +-------------------------------------------------------------------+
   |                            TABLE.md                               |
   |                                                                   |
   |  Current phase  |  Turn number  |  Current seat  |  Next action  |
   |  Candidate refs |  Active links |  Gate status   |  Open count   |
   +-----+-------------+----------+----------+-------------+-----------+
         |                        |                        |
         | reads                  | reads                  | reads
         v                        v                        v
   +-----------+            +-----------+            +-----------+
   |  PLANNER  |----------->|   PLAN    |----------->|   PLAN    |
   |           |  submits   | REVIEWER  |  approves  | CHALLENGER|
   +-----+-----+<-----------+-----+-----+            +-----+-----+
         |       findings         |                        |
         |                         |          clear         v
         |                         |                  +-----------+
         |                         |                  |   CODER   |
         |                         |                  +-----+-----+
         |                         |                        | submits
         |                         |                        v
         |                         |                  +-----------+
         |                         |                  |   CODE    |
         |                         |                  | REVIEWER  |
         |                         |                  +-----+-----+
         |                         |                        |
         |                         |             fixes      | approves
         |                         |          +-------------+
         |                         |          |             v
         |                         |          |       +-----------+
         |                         |          +-------|    QA     |
         |                         |            fails +-----+-----+
         |                         |                        |
         |                         |                        | passes
         |                         |                        v
         |                         |                  +-----------+
         +-------------------------+----------------->| DEPLOYMENT|
                    scoped return when needed         |   AGENT   |
                                                     +-----+-----+
                                                           |
                                        readiness only     | explicit owner
                                        until approved     | deploy approval
                                                           v
                                                     +-----------+
                                                     | VERIFY /  |
                                                     | COMPLETE  |
                                                     +-----------+

       Optional specialist seat:

       Current seat --> Assigned specialist     --> consultation artifact
                    <-- turn returns to caller  <---+
```

Arrows represent artifact-backed handoffs, followed by a short direct session
notification. These seats are examples rather than a universal six-agent
roster, but an implementation plan requires the distinct plan-challenger seat
shown above unless the owner recorded the permitted advance waiver.

## Dealer Responsibilities

The owner acts as the dealer for initial assignments and real owner decisions:

- creates/identifies the table or asks an agent to create and join it
- assigns roles to existing chats by exact session name or UUID
- provides the goal, authorized scope, and any explicit wait conditions
- avoids activating two agents for the same turn
- chooses a replacement chat if an agent is unavailable
- explicitly answers entries marked `owner decision required`
- may waive the adversarial plan challenge in advance only by saying `NO ADR`
  or `NO_ADR`; the plan reviewer records that direct instruction in the table
- provides production approval directly to the deployment agent in the same
  conversation in which that deployment would be executed

The dealer need not relay technical content or activate every turn. An initial
assignment can be as short as:

```text
Drop into the table at
/absolute/path/to/repo/agent_tables/<workstream>/TABLE.md
as the code reviewer. Take the current turn under the table rules.
```

If another seat owns the current turn, the joining agent registers and yields
until a handoff arrives. That is normal, not a reason to ask for manual
activation. Resolve genuinely conflicting assignments with the owner rather
than taking someone else's turn.

## Required `TABLE.md` Content

`TABLE.md` is a compact index and state record. It must not absorb the contents
of plans, reviews, test logs, or agent conversations.

Record role-to-session mappings, authorized scope, explicit owner pauses, and
notification/claim status alongside the turn. Prefer a session UUID once the
participant has joined; until then use the owner's exact session name. New Rally
tables keep this state in one helper-managed block in `TABLE.md`. The legacy
Markdown example below remains supported; do not create a competing state file.

A table should contain:

```markdown
# <Workstream> Agent Table

- Protocol: Agent Table, direct handoff
- Dealer: owner
- Phase: code review
- State: changes requested
- Turn: 7
- Current seat: coder
- Return seat: code reviewer
- Open blocking findings: 2
- Owner decision required: no

## Candidate

- Worktree: `/absolute/path/to/worktree`
- Branch: `feature/example`
- Base ref: `origin/main`
- Candidate refs:
  - `ServiceA`: `<40-character SHA>`
  - `ServiceB`: `<40-character SHA>`
- Candidate scope: ServiceA and ServiceB changes only

## Active artifacts

- [Current plan](../../implementation_plans/090426/example-implementation-plan-20260904.md)
- Plan viewer: `http://127.0.0.1:8765/plan/090426/example-implementation-plan-20260904.md`
- Current plan version: `v2`
- [Current code review](reviews/2026-09-05-code-review-r01.md)

## Latest handoff summary

The coder addressed `CR-001` and `CR-003` in the candidate refs above. The
authentication fallback now fails closed, and the affected integration and
configuration tests pass. Exact commands and results are linked from the plan
or current review evidence where applicable.

## Gate status

- Plan review: approved for `v2` at plan commit `<40-character SHA>`
- Adversarial plan challenge: clear for `v2` at plan commit `<40-character SHA>`
- Code review: changes requested for candidate refs above
- QA: waiting
- Deployment readiness: waiting
- Production approval: not requested

## Current assignment

Address `CR-001` and `CR-003`. Re-run the affected tests, create a new candidate
commit, update the candidate refs and brief handoff summary, and hand the turn
back to the code reviewer.

## Completed rounds

- [Plan v1 review R1](reviews/2026-09-04-plan-review-v1-r01.md): changes requested
- [Plan v2 review R2](reviews/2026-09-04-plan-review-v2-r02.md): approved
```

The `Current assignment` must be executable without interpreting old table
history. `Latest handoff summary` is a short response from the agent that just
finished; it is not a transcript or a substitute for the linked artifact.
Completed rounds contain only links and outcomes.

Every table with an implementation plan initializes the adversarial plan
challenge as `required` or `waiting`. The only waiver is a direct, advance owner
instruction using `NO ADR` or `NO_ADR`. Record it as `Adversarial plan
challenge: waived by owner - NO_ADR`, with the affected scope and provenance in
the table. Do not infer a waiver from urgency, simplicity, permission to
continue, or another agent's request. Without that exact recorded waiver, an
ordinary plan approval must proceed to `plan_challenger`, not implementation.
Mentioning the tokens while discussing, documenting, or testing this protocol
is not a waiver; the owner instruction must clearly apply to the current table
or plan scope.

A gate cannot read `approved`, `clear`, or `passed`, and a table cannot reach `complete`,
without a linked dated artifact for that gate: a review file, QA report, or
deployment-readiness note stating at minimum its verdict and what was checked.
For a plan or code review, `approved` specifically means the completed
Approval Receipt below; for an adversarial plan challenge, `clear` means the
gate receipt required by its agent contract. Raw logs, screenshots, or a
chat summary are evidence to link from that artifact, not a substitute for it.
A table with real shipped changes and no such artifact for a gate it claims
passed is not complete; it is unreviewed.

Before marking a table complete, the closing seat, the reviewer granting the
table's final required gate approval (code reviewer, QA, or deployment agent,
whichever is last for that table's scope, never the coder or planner), runs
[list-stale-worktrees.sh](../scripts/list-stale-worktrees.sh) for every
worktree the table used and records in the completion artifact that each one
is already removed or still needed and why, per the worktree cleanup rules in
`AGENTS.md`'s Collaboration Rules. This confirms the coder's own per-round
cleanup duty (see Coder, below) actually happened rather than duplicating it.
A table is not complete while it leaves a merged worktree registered with no
recorded cleanup check.

If the approved change affects a service with a local dev-serving lane, the
closing seat also leaves that service running the exact approved candidate
refs in its normal local lane and normal auth mode, for example the API on its
usual dev port and the UI on its usual dev port, not a QA-only auth mode or an
alternate port. Restore the repo's normal local auth lane per its own QA seed
cleanup rules first if QA left it altered. Record
in the completion artifact that it is running and how to reach it. The owner
must be able to open the change locally and check it without doing setup
themselves; a table is not complete while its API/UI candidate is left stopped
or reachable only through an altered QA lane.

## One Canonical Implementation Plan

There is exactly one implementation-plan file for the requested work. It should
remain in the repository's normal implementation-plan location, for example:

```text
implementation_plans/090426/example-implementation-plan-20260904.md
```

Do not create `implementation-plan-v1.md`, `implementation-plan-v2.md`, copied
plans inside reviews, or competing planner documents. The canonical plan is
updated in place.

When citing the plan in `Active artifacts`, a handoff, or an approval record,
link both the `.md` file and its local viewer URL at
`http://127.0.0.1:8765/plan/<path-relative-to-implementation_plans>` (the
default port of `scripts/serve_implementation_plans.py`). The viewer is a formatted read; the `.md` file
is the exact reviewed source. Quickly confirm the URL actually resolves before
sending it to the owner; if the local server is not running, start it or say
so instead of handing over a dead link.

The first complete plan is `v1`. Each time the planner changes the plan in
response to review, new evidence, or an approved scope change, it increments the
version by one before resubmitting it:

```text
v1 -> plan review -> v2 -> plan review -> v3
```

The top of the plan must identify:

```markdown
- Plan version: v2
- Updated: 2026-09-04
- Status: in review
- Responds to: [Plan v1 review R1](../reviews/2026-09-04-plan-review-v1-r01.md)
```

The plan should keep a concise revision history. Each entry names the version,
date, triggering review or decision, and a short summary of material changes.
It should not reproduce review findings in full.

```markdown
## Revision history

- `v1`, 2026-09-04: Initial researched plan.
- `v2`, 2026-09-04: Addressed `PR-001` and `PR-002`; added rollback and
  production feature-flag wiring.
```

When the planner hands off a version, it links the canonical plan from
`TABLE.md`, records the current version, and adds a brief summary or response in
`Latest handoff summary`. The summary explains what changed and which findings
were addressed. The actual plan remains authoritative.

Each submitted plan version should have an exact reproducible identity. Record
the commit containing that version, and optionally its content hash, before the
reviewer begins. This allows an immutable review to remain tied to `v1` after
the canonical file has advanced to `v2`.

## UI presentation approval gate

Any user-visible presentation change must be covered by an independently
reviewed and approved UI section in the plan before implementation. This includes
new or changed components, copy, labels, error/status messages, layout, styling
and responsive behavior, including changes discovered while fixing tests.

Inspect the affected UI and existing design patterns first. The plan must name
the touched surfaces and visible states, proposed exact copy, component reuse,
layout/spacing, typography/color, icon alignment, desktop/mobile behavior and
accessibility (including focus, status announcements and touch targets where
relevant). Give concrete styling choices or references to existing styles, not
just "make it consistent" or "polish later". Use a small mockup only when it
materially clarifies the design. Specify rendered acceptance checks.

When the change touches a shared design token, CSS custom property, utility
class, or reusable component, name every other consumer of that same surface
and state whether each one was checked, not only the touched screen. A shared
surface approved against one consumer routinely resurfaces as a defect in the
next one; enumerating consumers up front is cheaper than a separate fix commit
per consumer discovered later.

The reviewer must explicitly approve that UI scope against the identified plan
version before coding starts. General feature/test approval or permission to fix
a defect does not approve an unplanned presentation decision. If visible scope
emerges later, add it to the existing plan and obtain focused approval first;
continue unaffected work. An already approved design may be implemented and
corrected within its stated choices without repeated plan reviews. Only an
explicit owner waiver for the affected UI scope bypasses this gate.

If unplanned UI edits already exist, preserve them as an unapproved draft, stop
further implementation of that UI slice and submit its design for review; do not
silently treat it as approved or revert someone else's work. Before final code
approval, verify the actual rendered affected states on desktop and mobile
against the approved design and link screenshot artifacts in the review/handoff.
Capture desktop and mobile screenshots of the affected visible states. For
changes to existing UI, include comparable before/after screenshots using the
same viewport, state and representative data where applicable; capture the
baseline before editing when possible. For entirely new UI, capture the new
states and the prior placement/context when useful. If a before image cannot
be reproduced, state why rather than fabricate it. Identify candidate/base
refs, viewport and state with the artifacts so the comparison is reproducible.
Keep screenshots local/generated and link them from the authored evidence;
do not commit image artifacts unless the owner explicitly requests it.
Passing functional tests alone is not visual approval.
No extra reviewer seat, separate design document
or bookkeeping-only approval round is required.

## Immutable Dated Reviews

Every plan review, code review, and re-review is a new dated artifact. A
completed review is never edited by the planner, coder, or a later reviewer.
Every review artifact links back to the one canonical implementation plan. A
plan review identifies the plan version it directly evaluates; a code review
identifies the approved plan version governing the implementation.

Use ISO dates and include the reviewed plan version for plan reviews:

```text
reviews/2026-09-04-plan-review-v1-r01.md
reviews/2026-09-04-plan-review-v2-r02.md
reviews/2026-09-05-code-review-r01.md
reviews/2026-09-05-code-review-r02.md
```

If several artifacts of the same kind are created on one date, the round
number keeps the filenames unique and ordered.

A plan-review artifact must link back to the canonical plan and record the
exact version and commit it reviewed:

```markdown
# Plan Review: v1, Round 1

- Date: 2026-09-04
- Plan: [Canonical implementation plan](../../../implementation_plans/090426/example-implementation-plan-20260904.md)
- Reviewed plan version: `v1`
- Reviewed plan commit: `<40-character SHA>`
- Verdict: changes requested
```

The relative plan link will eventually open the newest canonical version; the
recorded version and commit identify the historical content evaluated by that
review. Reviewers must not claim approval without that identity.

After receiving findings, the planner updates the same plan to the next
version. The planner does not edit the old review or create a second plan. Its
brief response goes in the table handoff summary, while the plan revision
history records the durable high-level change.

## Turn Rules

### One Seat Owns The Turn

Only the role named in `Current seat` may perform workflow-changing work. Other
agents may inspect or safely register their assigned seat, but must not change
artifacts, code, gate status, or the next assignment. An explicit owner pause
can be recorded by any participant and invalidates the outstanding turn.

### The Turn Number Prevents Stale Work

The turn is a monotonically increasing integer. An agent records the turn it
accepted and re-reads `TABLE.md` immediately before completing its handoff.

If the turn number or current seat changed while the agent was working, the
agent must not overwrite the table. It should preserve any useful work in a
clearly marked draft artifact and report the stale-turn condition. Do not restart
the work or overwrite the newer assignment. Check current state before material
actions as well as at handoff; a table pause cannot interrupt an already running
tool by itself.

### A Turn Ends With A Handoff

To finish a turn, the seated agent must:

1. complete its assigned work
2. write or update the appropriate linked artifact; a reviewer always creates a
   new immutable dated review
3. identify the exact plan revision or candidate refs it evaluated or produced
4. replace `Latest handoff summary` with a brief summary or response for this
   turn
5. update the gate outcome
6. increment the turn number
7. assign the next seat and next action
8. re-read the final table to confirm the links and state are coherent
9. notify the next registered session directly, then yield and tell the owner
   the outcome, table path, and next seat; no manual activation is required

Write the artifact first, update the table second, and queue the notification
last. Include table identity, turn, and recipient role; detailed instructions
belong in the table. Record that the notification was queued, not that it was
processed. Do not resend accepted notifications just because there is no reply.
Recipients claim the current turn before working; ignore stale or duplicate
notifications without an ACK loop. A newer owner pause always wins over an old
queued approval. New Rally tables enforce these state checks through the helper;
legacy tables must record equivalent claim and notification state in their
existing format.

The final chat response is a notification, for example:

```text
Turn 7 is complete. I addressed CR-001 and CR-003 and handed turn 8 to the code
reviewer. The authoritative state and links are in <absolute TABLE.md path>.
```

It must not be necessary to copy the rest of that response anywhere.

### No Orphaned Next Step

Before ending a turn or completing a table, every unfinished in-scope action
must have a named responsible agent and an actionable handoff sent through the
existing mechanism. Hand an artifact awaiting review to its reviewer; do not
leave it behind a completed table. Raise an owner-only blocker as an explicit
decision request. Execution restrictions do not pause authorized preparation
or review.

Do not end a turn with a stated intention to implement, review, or coordinate
unless that work was actually performed, or was explicitly paused with a
`pause_reason` naming the exact blocker. Announcing what you are about to do
is not the handoff; the handoff is the completed work, or a precise statement
of why it could not be completed. A turn that ends on a sentence like
"implementing now" with no artifact, diff, or pause reason behind it has not
advanced the table, whatever it looks like in the chat transcript.

### No Hidden Handoffs

Material conclusions, findings, scope changes, assumptions, test results, and
unresolved questions must be recorded in artifacts before the turn changes.
An agent may not leave essential information only in its chat response.

### No Self-Approval

The agent that authored a plan cannot approve the plan. The agent that wrote or
fixed code cannot approve the code. The agent that performs QA cannot convert a
failed test into an accepted exception. Owner decisions and exceptions must be
recorded explicitly.

The same session may occupy the planner and coder seats for continuity. It
must not also occupy the ordinary plan-reviewer or plan-challenger seat for the
same work. The ordinary plan reviewer and plan challenger must also be distinct
sessions from each other.

## Standard Seats

Use only the roles and gates needed for the authorized task. Every
implementation plan requires a distinct `plan_challenger` session after
ordinary plan approval unless the table records the owner's advance `NO ADR`
or `NO_ADR` waiver. The examples below do not otherwise require extra agents,
plans, specialist reviews, or approval-record-only commits.

### Planner

The planner researches the requested change and produces the implementation
plan. It must follow the repository's implementation-plan and product-rule
provenance requirements, including inspecting the relevant code, contracts,
tests, configuration, runbooks, and deployment or data/content-release surfaces.

If the work involves UI changes, particularly new components, the plan must
meet the UI presentation approval gate above. Do not leave brand consistency,
exact copy or UX quality for the coder to improvise during implementation.

The planner owns:

- the implementation plan
- the inspected-surface inventory
- explicit assumptions and owner decisions required
- proposed implementation sequence
- validation and rollback plan
- the initial candidate scope

The planner does not approve its own plan. When ready, it records the exact plan
version and commit, links the same canonical file, adds a brief handoff summary,
and hands the turn to the plan reviewer.

### Plan Reviewer

The plan reviewer independently checks whether the plan is implementable,
complete, correctly scoped, and grounded in inspected repository truth.

The plan reviewer must:

- read `TABLE.md` and the exact linked plan
- inspect important cited code and runbook surfaces rather than trusting the
  planner's summary
- separate verified existing rules from proposals and owner decisions
- for a UI-touching plan, especially one introducing new components, verify
  it actually addresses brand consistency and UX quality rather than treating
  the change as pure implementation mechanics
- explicitly approve its visible scope and design under the UI presentation
  approval gate, or return the missing design decisions as findings
- assign stable finding IDs such as `PR-001`
- state what evidence would close each blocking finding
- produce one review artifact for the round
- return either `approved`, `changes requested`, or `owner decision required`,
  with the Approval Receipt below for an `approved` verdict

Approval applies only to the reviewed plan version and commit. Any subsequent
plan update increments the version and requires a new dated review round.

On approval, the plan reviewer must inspect the table's adversarial gate. With
no valid recorded owner waiver, it advances the turn to `plan_challenger`, not
the coder, and notifies the registered challenger session. If the challenger
has not registered yet, leave the turn ready for `plan_challenger` and give the
owner the table ID; do not reroute to implementation. With a valid advance
waiver, record `waived by owner - NO_ADR` and hand the approved plan to the
coder.

### Plan Challenger

The plan challenger follows
[Agent_AdversarialPlanReviewer.md](Agent_AdversarialPlanReviewer.md) after the
ordinary reviewer approves the exact plan version and before implementation.
It must be a separate session from both the planner and ordinary plan reviewer.

The owner may start that session before its turn with only the table ID. It
locates the unique table, joins as `plan_challenger`, and stands by when another
role owns the turn. Standby means no substantive review, no early reading of
the ordinary review's reasoning, and no polling. The reviewer handoff and Rally
notification cause it to re-read the table, claim the current turn, and begin.

The challenger starts blind to the ordinary review's reasoning. It first
reconstructs the owner outcome, actual customer and system journey, affected
inventory and consumers, existing mechanisms, smaller alternatives, important
assumptions, and second- and third-order effects from the owner request, exact
plan, inspected source, and rendered/runtime evidence. It then reads the
ordinary review to detect shared framing errors without duplicating resolved
findings.

The challenger writes one dated adversarial review artifact with stable
`APR-###` findings and returns exactly one verdict:

- `clear`
- `changes requested`
- `owner decision required`

A blocking finding needs a concrete reachable failure or violated owner
requirement, affected users/data/invariant, traceable evidence, and closure
proof. There is no finding quota. The challenger is read-only with respect to
the plan and product code and does not replace ordinary plan approval or a
domain specialist.

When changes are requested, the planner revises the same canonical plan, the
ordinary reviewer performs a focused re-review, and the challenger then
performs a focused closure review. Do not add a reviewer of the challenger or
restart unrelated approvals.

### Coder

The coder implements the approved plan in the table's designated worktree and
branch. Before starting, the coder must verify either that the adversarial
challenge is clear for the same exact plan identity or that the table records
the owner's valid advance `NO ADR`/`NO_ADR` waiver. The coder must preserve
unrelated existing changes and obey all repository-specific instructions.

Implement the full approved plan end to end, including every milestone in it,
and complete its local verification before handing off. Do not hand off one
step, file, or milestone at a time, and do not treat a milestone inside the
plan as its own handoff checkpoint. The plan was written in meticulous detail
precisely so the coder can execute it in one pass; splitting that into a
sequence of review round-trips defeats the purpose of planning it that way.
Hand back early only for a genuine blocker, missing information, a real owner
decision, or a material departure from the approved plan, never to checkpoint
routine progress.

The coder owns:

- product and source changes authorized by the approved plan
- migrations, tests, configuration, and documentation required by that plan
- local verification appropriate to the change
- concise table responses to review or QA findings, with separate evidence only
  when the linked plan, commits, and test references are insufficient
- exact candidate refs for every affected repository

The coder may mark a finding `addressed` with evidence. It cannot mark a review
finding `verified` or `closed`.

Any material departure from the approved plan returns the table to plan review
unless the plan already authorizes the variation.

Once the candidate is merged through the repository's normal push/PR/merge
workflow, the coder must clean up any temporary worktree it created for this
table's work in the same session: confirm the worktree's commit is contained
in the merged target or identify the exact merged pull request, check for
uncommitted, staged, untracked, or unrecognized ignored changes before
removing anything, then remove the worktree and run `git worktree prune` in
the owning repository. Follow the repository's applicable `AGENTS.md`/
the repository instruction file (`AGENTS.md` / `CLAUDE.md`) worktree-removal
safety checks in full; do not skip them just
because the table shows the candidate approved and merged. Do not leave a
merged worktree and its duplicated build caches or dependencies on disk
merely for convenience.

### Code Reviewer

The code reviewer reviews the exact candidate refs, not the coder's description
of them. It should remain read-only with respect to product code unless the
dealer explicitly reassigns it to the coder seat in a later turn.

The code reviewer checks:

- correctness and regression risk
- agreement with the approved plan
- UI design approval provenance and desktop/mobile rendered evidence for
  affected presentation states, not merely passing functional assertions
- tests and meaningful missing coverage
- security, data integrity, failure handling, and rollback behavior
- cross-service, configuration, migration, and feature-flag wiring where
  applicable
- whether any code change invalidated an earlier plan assumption

Findings use stable IDs such as `CR-001`. Each finding identifies severity,
blocking status, file and line or component, rationale, and required proof.
An `approved` verdict requires the Approval Receipt below.

Approval is bound to the exact candidate refs in `TABLE.md`. A later product
code or configuration change invalidates that approval. Changes only to table
and review artifacts do not invalidate the code candidate when the candidate
refs and product diff remain unchanged.

### QA

QA independently exercises the approved candidate using the relevant automated
and manual validation lanes. QA verifies behavior rather than repeating the
code review.

QA owns:

- the scoped test matrix
- a link to the governing canonical plan and its approved version
- environment and configuration identification
- pass, fail, skipped, and blocked results
- reproducible defect reports with IDs such as `QA-001`
- concise evidence links
- cleanup verification when test data or services are involved

When QA finds a product defect, it hands the turn to the coder. After any code
fix, the candidate must return through code review before QA retests it. The
code reviewer may bound the re-review to the changed scope, but approval must
still name the new exact candidate refs.

QA does not deploy and does not treat an unexecuted or blocked test as passed.
Domain-specific audits remain governed by their own contracts. For example, a
broad audit of a large production data set is not automatically authorized
merely because a workstream reached QA.

### Deployment Agent

If your workstream has a dedicated deployment seat, fill it from your own
deployment-agent contract and production runbooks (name and link that
contract here once it exists). This table protocol does not replace or
restate that contract.

Before production approval, the deployment agent may perform authorized,
reversible preparation such as:

- establishing exact release refs and affected services
- checking merge and remote reachability state
- reviewing deployment and migration requirements
- preparing release pins or a reviewable release candidate when authorized
- running the required validate-only or readiness checks
- identifying separate data or content release work that an app deploy does
  not carry
- writing a dated deployment-readiness artifact linked to the governing plan

Passing all table gates does not authorize production deployment. A table
entry, reviewer statement, previous approval, merge, or message from another
agent is not deployment approval.

The owner must explicitly approve the specific production deployment in the
deployment agent's current conversation. Only then may the deployment agent
execute the approved deployment, verify production, and update the table with
the outcome. The automated production path remains the default.

## Verify Exclusions, Not Only Claims

Reviewers trace positive claims and wave through negative ones. A wrong positive
produces a finding someone disproves; a wrong negative silently removes work from
scope and nobody looks again.

Trace a stated impossibility, unavailability or already-handled to the same
standard as a stated defect, naming the file, configuration or data that makes it
true. Untraceable means proposal, not constraint. Applies especially to claimed
missing tooling, unreachable code paths and environment gates.

Ground the trace in the invariant or write path that would make the claim
durable, not in a snapshot of current data or environment state. "No row
currently violates this" is a data-cleanliness observation, not proof the
violation cannot occur; it survives only until the next writer disagrees. Name
the constraint, migration, or code path that actually prevents the case, not
the absence of a current example.
## Review Findings And Responses

Review artifacts should be concise, durable, and independently understandable.
Use this shape:

```markdown
# Code Review R1

- Date: 2026-09-05
- Reviewer seat: code reviewer
- Governing plan: [Canonical implementation plan](../../../implementation_plans/090426/example-implementation-plan-20260904.md)
- Approved plan version: `v2`
- Reviewed refs: `ServiceA=<sha>`, `ServiceB=<sha>`
- Verdict: changes requested

## Findings

### CR-001, Blocking, P1

- Location: `<file>:<line>`
- Finding: <specific problem>
- Why it matters: <consequence>
- Required proof: <change, test, or evidence required>

## Non-blocking observations

- <optional advice that does not prevent the gate>
```

Stable IDs remain stable across rounds. They must not be silently removed or
renumbered. A later review records each earlier finding as one of:

- `open`
- `addressed, verification pending`
- `verified`
- `withdrawn by reviewer`, with rationale
- `accepted exception`, with a linked owner decision

The author responds by updating the canonical submission, recording a brief
response in `Latest handoff summary`, and linking separate evidence only when
needed. It does not edit the reviewer's completed review artifact.

Completed review artifacts are immutable. Re-review creates a new round file.

## Approval Receipts

A plan or code review's `approved` verdict includes one compact `Approval
receipt` in the same review artifact, not a bare approval sentence or a link
to evidence. When the disposition is `approved`, show the same receipt in
`Latest handoff summary` and any owner-facing result.

Build the receipt from the actual scope instead of a fixed universal
checklist. It contains:

- a small core covering the exact reviewed plan version or candidate identity,
  independent inspection of the affected surface, applicable acceptance
  evidence, residual findings, and the next actor
- one row for each material scope-specific acceptance dimension; for UI work
  this normally includes desktop rendering, mobile rendering, full-page
  context and adjacent content, relevant states, interaction and
  accessibility behavior, and icon alignment when icons changed or are part
  of the reviewed surface
- evidence and provenance on every row, using precise labels such as
  `reviewer-inspected`, `reviewer-run`, `retained from <exact review
  identity>`, or `implementer-reported`

Use Markdown checkboxes so the state is visible:

```markdown
### Approval receipt

- [x] Exact reviewed scope and identity. Evidence: commit/tree or plan SHA and
  scoped diff. Provenance: reviewer-inspected.
- [x] Desktop and mobile affected states. Evidence: viewport, state, and local
  artifact paths. Provenance: reviewer-inspected.
- [x] Affected verification. Evidence: exact command and result. Provenance:
  reviewer-run.
- [x] Residuals and next actor. Evidence: none, or the listed non-blocking
  observations; next actor is explicit. Provenance: reviewer-inspected.
```

An implementer-reported claim alone cannot satisfy a material row.
Independently inspect or reproduce it, or leave the row unchecked. Retain
prior evidence only when its exact reviewed identity and affected behavior are
unchanged, and name that prior review. Do not pad the receipt with
inapplicable rows or check an unknown.

`approved` requires every required row checked; non-blocking observations may
still be recorded alongside it. If any required row is unchecked, the verdict
is `changes requested`, naming the concrete blocker and which prior approvals
remain valid. For a focused re-review, show the complete current receipt but
cite retained evidence for unchanged rows instead of rerunning unrelated work.

Keep the receipt inside the normal review artifact. Do not create a second
approval artifact, add another reviewer seat, or introduce an
approval-of-the-approval turn solely to maintain it. The plan challenger is a
separate required product-and-systems challenge, not a duplicate receipt or an
approval of the ordinary reviewer.

## A Finding Is Authoritative; Its Suggested Fix Is Not

A finding states a defect. Any wording or patch the reviewer suggests alongside it
is advice; the implementer owns the fix.

Departing from a suggestion is fine when it resolves the finding, is stated in the
handoff rather than applied silently, and can be reverted on request. Reviewers
judge whether the finding is resolved, not whether their wording was used.
## A New Regression Test Must Be Proven To Fail First

A test that passes before its fix certifies the defect. Restore the pre-fix
behaviour, watch the test fail for the stated reason, and report that you did.

When two defects interact, prove each test fails independently: one defect can
mask another and produce a green result for the wrong reason. The same applies to
a new assertion, which must fail when its invariant is violated on purpose.

## Blast Radius Sets The Rigor Floor

A production write path shared by multiple writers, a payment or entitlement
path, or a shared design-token/component surface requires deliberate,
sequenced verification: trace the governing invariant or write path, enumerate
the affected consumers, and do not approve on a partial trace. This is a floor
set by what is actually at risk, not a target to negotiate down under time or
turn-count pressure.

Meeting that floor is not measured by turn count, artifact volume, or
screenshot count. A review is judged by whether it actually traced the claimed
exclusion or invariant to its ground truth, not by how much it produced getting
there. A long, expensive review that still finds its defect late is a
sequencing failure, not proof the floor was met: front-load cheap structural or
shape checks, such as whether inputs match the expected shape or a fixture
behaves like the real dependency it replaces, before spending on expensive
semantic review of a high-risk path. Do not add turns, rounds, or reviewer
seats merely to look thorough; that is not the same as meeting the floor
above.
## Candidate Identity

Every approval and QA result must identify exactly what was evaluated.

For a single repository, record the base and candidate commit. For a multi-repo
change, record every affected repository and commit independently. Do not use
phrases such as `latest branch`, `current main`, or `the code above` as candidate
identity.

If an agent discovers an uncommitted candidate, it may inspect it but cannot
issue final approval unless the review artifact records an exact reproducible
diff identity. The normal handoff should use committed candidate refs.

## Standard Workflow

### 1. Open The Table

The owner, or an agent explicitly asked to create and join, establishes the
workstream, scope, shared worktree/repository location, named participants, first
assignment, and turn 1. The standard workflow below is illustrative; use only
the stages the task actually needs.

### 2. Plan

The planner researches and writes the single canonical plan as `v1`, updates
the active plan link and brief handoff summary, and hands the table to the plan
reviewer. A later planner turn updates that same file to `v2`, `v3`, and so on.

### 3. Review The Plan

The plan reviewer either:

- approves and hands the turn to the plan challenger, unless the table records
  the owner's valid advance `NO ADR`/`NO_ADR` waiver, in which case it records
  the waiver disposition and hands the turn to the coder
- requests changes and returns the turn to the planner
- requests a specialist consultation and returns control to itself afterward
- requests an owner decision and stops

Plan and review may loop for as many evidence-producing rounds as needed. If
the same substantive disagreement survives three rounds without new evidence,
the table should request an owner decision rather than continue the loop.

### 4. Challenge The Approved Plan, Unless Owner-Waived

The plan challenger follows its blind-first sequence and either:

- clears the exact approved plan and hands the turn to the coder
- requests changes and returns the turn to the planner
- requests an owner decision and stops the affected work

After a revision, ordinary focused re-review precedes focused adversarial
closure. Only the owner's advance `NO ADR` or `NO_ADR` instruction, recorded in
the table, may skip this stage.

### 5. Implement

The coder implements the full approved plan in one pass, verifies locally,
records exact candidate refs, and hands the turn to the code reviewer. It does
not hand off after an intermediate, untested slice.

### 6. Review The Code

The code reviewer approves, requests changes, requests consultation, or asks
for an owner decision. Code and review loop until the exact candidate is
approved.

### 7. Run QA

QA tests the approved candidate. Failure returns to the coder, then code review,
then QA. Passing QA hands the turn to the deployment agent.

### 8. Establish Deployment Readiness

The deployment agent checks the relevant runbooks and prepares a reviewable
deployment decision. It may return defects or missing evidence to the coder,
reviewer, or QA seat.

If production execution is requested, the deployment agent stops at the
approval boundary until the owner gives explicit approval in that deployment
chat.

### 9. Deploy And Verify, When Explicitly Approved

The deployment agent uses the approved production lane, records exact deployed
refs, completes post-deploy verification, identifies any separate data or
content release state, and marks the table complete or routes a failure appropriately.

## Specialist Drop-In Rules

Any normal seat may request a bounded specialist review. Examples include
security, database, accessibility, domain/product expertise, content quality,
or a particular service owner.

Route a bounded question directly to an existing owner-assigned specialist.
Adding a new agent, scope, or mandatory gate needs the relevant owner authority;
do not infer it from this example. Before the handoff, `TABLE.md` must state:

- the specialist role
- the exact question
- the linked inputs
- the return seat
- whether the consultation is advisory or an explicit gate

The specialist writes a consultation artifact, increments the turn, and returns
the table to the recorded return seat. It does not take over the workstream,
expand its own scope, edit product code, or approve another role's gate unless
the table explicitly assigns that authority.

Link your own established specialist contracts here as your team creates
them, for example a domain-expertise contract for user-facing behavior in
your product, a bounded-audit contract for a sensitive data surface, or a
release/production-deployment contract.

## Owner Decisions

An agent requests an owner decision only when available evidence cannot resolve
a consequential choice. The requesting artifact must contain:

- the exact decision
- why inspected code, tests, runbooks, and prior decisions do not resolve it
- viable options and concrete consequences
- the requesting agent's recommendation, if it has one
- the seat to resume after the decision

Record the decision in a linked artifact and resume the recorded return role
directly once the owner answers, unless the owner imposed another stop. Do not
add a separate activation or approval-record review ceremony.

Production deployment approval is different from an ordinary owner decision:
it must be communicated directly in the deployment agent's current conversation
and cannot be inherited solely from the table artifact.

## Joining An Existing Table

Every agent joining a table must perform this entry sequence:

1. read the repository's applicable `AGENTS.md` files
2. use `$rally` when available and consult this strategy for applicable role rules
3. read the entire `TABLE.md`
4. confirm its role/session mapping; register and yield if another seat owns the turn
5. claim the current turn, checking table identity and rejecting stale/duplicate notifications
6. read the active artifacts needed for the current assignment, not all history
7. inspect the underlying source, tests, configuration, or runbooks required by
   its role rather than trusting artifact summaries blindly
8. execute only `Current assignment`

An agent must not restart the workstream from scratch merely because its chat
lacks history.

## Owner Prompts

### Create And Join With Rally

```text
Use $rally to create table <name> and join as reviewer. The implementer is the
existing session <exact session name>. Our goal is <goal>; authorized scope is
<scope>. Coordinate directly. Wait for me only on <explicit stops, if any>.
```

The creating agent records these assignments, registers itself, and notifies the
first assigned session. No new chat is spawned and no live table is replaced.

### Seat An Agent

```text
Drop into the Agent Table at <absolute path to TABLE.md> as the <seat>. Read the
applicable AGENTS.md instructions and Agent Table rules, verify that the table
assigns the current turn to your seat, complete the current assignment, write
all material results to linked artifacts, update the table, and hand off to the
next seat. Do not rely on or ask me to paste another agent's chat response.
```

### Return A Prior Agent To The Table

```text
Return to <absolute path to TABLE.md> in your existing <seat> role. Another
agent has completed the intervening turn. Re-read the table and active artifacts
instead of relying on your prior chat context, then take the current assignment
if the table assigns it to you.
```

### Seat A Specialist

```text
Drop into <absolute path to TABLE.md> as the temporary <specialist> seat. Answer
only the consultation question recorded in the table, write the consultation
artifact, and return the turn to the recorded return seat. Do not take over the
main gate or edit the implementation.
```

## Failure And Recovery

### Agent Becomes Unavailable

The owner may assign a new chat to the same seat. Record the explicit replacement,
update the session binding, invalidate the old claim by incrementing the turn,
and notify the replacement. The replacement reads the table and relevant
artifacts, not a chat transcript. Do not silently steal an occupied seat.

### A Returning Seat Keeps Its Name But Not Its Claim

A restarted or reconnected seat returns under the same name with a new session
identity. Claims bind to the identity, so it can look present and reachable while
being unable to take the turn it held.

The seat not holding the turn invalidates the stale claim by advancing the turn,
then reissues with the new number. Do not resume the old turn. Restart before a
turn is claimed where the choice exists.
### Follow-Up Work Arrives After A Table Is Complete

A completed table cannot be reopened and should not be. Do not manufacture a pause
to force one open, and do not create a second table for the same goal.

Send the assignment directly with enough context to act without the table, say
explicitly that the message is the assignment and that the table was deliberately
not reopened, and keep the original artifacts authoritative. Follow-up needing its
own plan and several turns is a new workstream with a distinct goal.
### Agent Modified Work Without The Turn

Do not merge the state changes automatically. Preserve the work for inspection,
record the last unambiguous state without decreasing the turn number, and let
the owner decide whether the work becomes a linked draft, is discarded, or is
resubmitted in a new turn.

### A Notification Is Not A State Change

Write the result as a durable artifact, update the table, notify last. A message
carries no authority and records nothing.

Worse than silence is a message describing a transition that did not happen, which
leaves the table saying the work was never reviewed. The receiving seat must
refuse to repair it by writing the other seat's state; name the missing command
and hand it back. Before yielding, confirm the table reflects what you did.
### Table And Artifact Disagree

Stop the affected handoff. Record the discrepancy without guessing and route
it to the responsible registered role if the correction is already authorized.
Ask the owner only when resolving it needs a new decision or authority.

### Candidate Changed During Review

The reviewer stops and marks the review stale. The coder submits stable exact
candidate refs in a new turn. Findings already proven against unchanged code may
be carried forward explicitly, but final approval must bind to the new refs.

### Review Loop Stalls

After three rounds of the same substantive disagreement without new evidence,
the current reviewer writes an owner-decision request. Rephrasing a finding does
not reset this count.

### QA Environment Is Blocked

QA records the exact blocker and the unexecuted scope. The table must say
`blocked`, not `passed`. Route an authorized fix to the coder or an already
assigned specialist; no later gate may reinterpret missing QA as success.

## Direct-Handoff Boundaries

Direct handoff intentionally does not provide:

- automatic polling or filesystem watching
- concurrent ownership of a turn
- automatic conflict resolution
- majority voting or model-council decisions
- a general agent with authority to override role-specific gates
- implied production approval

Native queueing notifies the named session after the durable handoff; the owner
does not activate each turn. Explicit waits, one-turn ownership, candidate
identity, independent review, and production-approval boundaries remain intact.
If transport is unavailable or uncertain, preserve the pending handoff, inspect
current state, and report the narrow blocker. Do not add a watcher, background
retry loop, or repeated probes as an automatic fallback.

## Definition Of A Successful Table

The protocol is working when:

- the owner supplies initial role/session assignments, not recurring handoffs
- a fresh agent can understand the current assignment from the table and links
- the main table remains short enough to scan quickly
- review history is preserved without bloating the table
- findings have stable identities and explicit dispositions
- approvals identify exact plan or code revisions
- coder, reviewer, and QA authority remain independent
- a missing chat does not destroy workflow context
- deployment rules and explicit approval boundaries remain intact
- the completed table explains what was planned, reviewed, implemented, tested,
  approved, deployed, and verified
