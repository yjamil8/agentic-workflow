# Story plan: S01 <story title>

- Plan version: v1
- Updated: YYYY-MM-DD
- Status: <draft | in plan review | approved for vN | changes requested (PR-001)>
- Agent Table: agent_tables/<feature-slug>-s01/TABLE.md (table ID <uuid>)
- Plan viewer: http://127.0.0.1:8765/plan/MMDDYY/<feature-slug>/stories/S01-<story-slug>-plan.md
- Source: implementation_plans/MMDDYY/<feature-slug>/stories/S01-<story-slug>-plan.md
- Story: implementation_plans/MMDDYY/<feature-slug>/stories/S01-<story-slug>.md
- Feature plan: <path>, version <vN> at <commit> (or "standalone story")
- Investigation: <path> at <commit> (or "standalone story")
- Repos: <repositories this plan changes>
- Effort: <rough estimate>
- Review gates: <challenge policy for this story, copied from TABLE.md, which is authoritative>

## Revision history

- `v1`, YYYY-MM-DD: Initial story plan.

## Outcome

<What this story makes true, as the user will experience it, taken from the
story. Then the most likely misreading and why it is wrong.>

## Inventory recheck

```bash
git log --oneline <investigation-sha>..origin/main -- <paths the investigation listed>
```

<What changed since the investigation, and any new call site, reader, or
writer found. "No changes" needs the command output that showed it. For a
standalone story, write the current-behavior evidence here instead, with the
searches and counts.>

## Departures from the feature design

<Anything this plan does differently from the approved feature plan, and why,
or "None". A departure needs owner approval before implementation and triggers
the adversarial challenge unless the owner waives it for this story.>

## Requirements and out of scope

| Requirement | Basis |
|---|---|
| <each acceptance criterion, restated as what must be true> | <story criterion or feature plan requirement> |

Out of scope:

- <From the story, plus anything this plan explicitly leaves alone.>

## Proposed changes

### 1. <Contract or surface>

<How it changes, and why the smallest existing mechanism is not enough if new
machinery is proposed.>

## Acceptance and verification

Acceptance scenarios:

- <Each story acceptance criterion as a concrete test or check, plus edge
  cases.>
- Each new regression test fails on the base commit before the change.

Verification:

```bash
<exact commands, and the result that counts as passing>
```

Local environment: <local database and Azure Storage (Azurite) setup and seed
data needed; never QA or a shared environment>.

## Risks and how not to misread results

- <Risk, how it would show up, and what signal would or would not indicate a
  problem.>

<Add any when-applicable section from implementation-plan-template.md whose
trigger applies to this story: owner decisions, inventory and compatibility
boundary, security, privacy, and compliance, feature flags and configuration,
UI presentation, rollback, delivery and authority, required updates, review
request. Delete this paragraph.>
