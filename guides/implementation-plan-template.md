# <Outcome-shaped title, for example "Merged accounts keep their in-progress work">

- Plan version: v1
- Updated: YYYY-MM-DD
- Status: <draft | in plan review | approved for vN | changes requested (PR-001, PR-002)>
- Agent Table: agent_tables/<workstream>/TABLE.md (table ID <uuid>)
- Plan viewer: http://127.0.0.1:8765/plan/MMDDYY/<slug>-plan-YYYYMMDD.md
- Source: implementation_plans/MMDDYY/<slug>-plan-YYYYMMDD.md
- Repos: <repositories this plan changes>
- Effort: <rough estimate, for example "about two days plus review">
- Responds to: <When applicable (v2 onward): link to the review this version answers.>
- Inspected source: <When applicable (shared code): <repo>@<40-character SHA> per repo; note unrelated local edits.>
- Review gates: <When applicable: gate state and any owner NO_ADR waiver, copied from TABLE.md. TABLE.md is authoritative.>
- Tracking ticket: <When applicable: issue or ticket ID.>

## Revision history

- `v1`, YYYY-MM-DD: Initial plan.

## Outcome

<Two or three sentences stating the decision as the user or operator will
experience it. Then the most likely misreading and why it is wrong.>

## Owner decisions required

<When applicable: any choice existing authority cannot resolve. Delete this
section otherwise. Keep it here, near the top, so blocking decisions are seen
first.>

1. D1: <exact decision>. Blocks: <yes, which milestone | no>. Options: <A,
   consequence; B, consequence>. Default if unanswered: <A>. Resumes:
   <seat>. Recommendation: <A, because ...>

## Current behavior and evidence

<Why this work is needed, traced to code and data.>

| Surface | Inspected behavior (file + symbol, line where precise) | Consequence |
|---|---|---|
| <component or endpoint> | `<path/to/file>` `<Symbol>` (`:123`) does X | <what goes wrong or must be preserved> |

Completeness: <the exact search, for example `rg -n "SymbolName" src/`, its
count, and how you know every call site, branch, writer, and allowlist entry
is covered>.

## Inventory and compatibility boundary

<When applicable: persisted data, an API or event contract, or its clients or
writers change. Delete this section otherwise.>

### Existing data

<Affected persisted data, with dated counts from the QA database (read-only,
labeled as QA). Production is not readable: say what the QA data cannot tell
you about production, and design for that unknown or name who can check it.>

### Active clients and writers

- <Every reader and writer, including cached web or mobile clients and
  deployed service versions that will keep sending the old shape.>

### Reuse decision

Reuse <existing mechanism>; it already provides <property>. Do not add
<table, service, endpoint, migration, framework>.

## Requirements and out of scope

| Requirement | Basis |
|---|---|
| <what must be true when done> | <owner instruction, existing invariant, or inventory> |

Out of scope:

- <Explicitly unchanged behavior, surfaces, and data, including non-goals.>

## Proposed changes

### 1. <Contract or surface>

<How it changes. If new machinery is proposed, why the smallest existing
mechanism is not enough, and what the change deliberately does not add.>

## Security, privacy, and compliance

<When applicable: authentication, authorization, secrets, personal data, or
regulated data are touched. Delete this section otherwise.>

- Trust boundaries and authorization checks affected: <...>
- Personal or regulated data: <what is read, stored, logged, or sent where,
  and retention>
- Secrets: <where they live; never in code, plans, or logs>
- Reviews your organization requires: <security, privacy, legal, or none>

## Feature flags and configuration

<When applicable: behavior is gated or configuration changes. Delete this
section otherwise. Flag, compile-time or runtime, default per environment,
every wiring surface from AGENTS.md "Feature Flag Wiring Discipline", and
local-development parity.>

## UI presentation, exact approved scope

<When applicable: required for any user-visible change, per the UI
presentation approval gate. Delete this section otherwise.>

| State | Exact copy | Interaction |
|---|---|---|
| <state> | "<exact string>" | <what happens> |

Reused components and styles: <names>. Breakpoints: <behavior per width>.
Accessibility: <focus, announcements, touch targets>. Icons: <centering and
text alignment>. Screenshot gate: <before/after states and viewports>.

## Milestones

<When applicable: two or more journeys that can each be demonstrated on their
own. Delete this section otherwise; acceptance then lives in the next
section.>

### Milestone 1: <User journey that works end to end>

<Scope across every affected layer for this journey.>

Acceptance:

- <Concrete scenario, including edge cases.>

### Milestone 2: <Next journey>

## Acceptance and verification

Acceptance scenarios:

- <Concrete scenario including edge cases: signed out, new, returning,
  partially complete, permission denied, concurrent, expired, stale cache,
  retry.>
- Each new regression test fails on the base commit before the fix.

Verification:

```bash
<exact commands, and the result that counts as passing>
```

Local environment: <local database and Azure Storage (Azurite) setup, seed
data, and configuration the commands need; never QA or a shared environment>.

Third-party services: <sandbox or test account used; if a double stands in,
how it matches the real service's responses and errors>.

## Rollback

<When applicable: data, a content release, configuration, a third-party
service, or anything else a code revert does not undo. Delete this section otherwise.>

1. Measure the blast radius first: <the QA result, labeled as QA, and the
   exact read-only query for someone with production access to run before
   rolling back>.
2. Ordered steps: <commands, in one transaction where data is involved; for
   content, re-run the GitHub Actions release workflow with the previous
   version>.
3. Kept and lost: <what rollback preserves, and accepted collateral>.

Invariant: <what must remain true after rollback>.

## Risks and how not to misread results

- <Risk, how you would detect it in production (metric, log, alert), and what
  signal would or would not indicate a problem.>

## Delivery and authority

<When applicable: a deploy, content release, third-party change, hotfix, multi-repo change, or any step needing separate approval. Delete this
section otherwise.>

- Branch and lineage: <worktree, branch, base; for a production hotfix, the
  exact commit currently deployed, per your release records>.
- Deploy: <services, environments, and order>.
- Content release: <the GitHub Actions release workflow, its inputs, and its
  order relative to the app deploy>.
- Change management: <change ticket or approval record, if your organization
  requires one>.
- Separate approvals: <each step needing explicit approval>. Plan approval is
  not merge or production approval.
- Stopping rule: <conditions that pause work and return to the owner with
  smaller alternatives>.

## Required updates

<When applicable: keep only the lines this change triggers under your team's
rules. Delete this section otherwise.>

- Tracking ticket status and next action.
- Runbooks and on-call documentation.
- User-facing documentation, help content, or release notes.
- API documentation or published contracts.
- Dashboards and alerts.
- Team agent instructions or skills (AGENTS.md, CLAUDE.md) when the workflow
  itself changes.

## Review request

<When applicable (v2 onward, or any re-review): what is new in this version,
what is retained from a prior approval, a disposition of each prior finding
by ID, and the limits of the evidence. Delete this section in v1.>
