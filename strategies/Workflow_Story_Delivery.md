# Workflow: Story Delivery

Takes one user story from plan to merged pull request through plan,
implementation, and review loops. Use it for a story produced by
[Workflow_Feature_Discovery.md](Workflow_Feature_Discovery.md), or for a
standalone story the owner provides.

It runs on the Agent Table protocol
([Agent_Table_Collaboration_Rules.md](Agent_Table_Collaboration_Rules.md)) and
agent-table transport, which still govern turns, handoffs, reviews, receipts, and
owner decisions. Use one table per story, so each table ends in one pull
request.

## Seats

| Seat | Role name on the table | Does |
|---|---|---|
| Implementer | `implementer` | Writes the story plan, then implements it. |
| Reviewer | `reviewer` | Reviews the story plan and the code; never the author. |
| Challenger | `plan_challenger` | Only when the challenge policy or a departure requires it. A different session from both others. |

## Artifacts

```text
<work-repo>/implementation_plans/MMDDYY/<feature-slug>/stories/
  S01-<story-slug>.md        the story (from Feature Discovery or the owner)
  S01-<story-slug>-plan.md   the story plan (from guides/story-plan-template.md)
<work-repo>/agent_tables/<feature-slug>-s01/
  TABLE.md
  reviews/
```

For a standalone story with no feature, use
`implementation_plans/MMDDYY/<story-slug>/` and `agent_tables/<story-slug>/`.

## Setup

The creating session records in a `## Owner policy` section of `TABLE.md`
(outside the agent-table managed block):

- the story file and, when the story came from Feature Discovery, the approved
  feature plan version and commit, the investigation commit, and the feature
  table path
- the challenge policy for this story: inherited from the feature table's
  recorded story policy, unless the owner states a different one now. For a
  standalone story, ask the owner. Never infer a waiver.

## Loop

### 1. Story plan

The implementer writes the story plan from the story plan template. It cites
the feature plan and investigation instead of repeating them, and it must
include:

- **Inventory recheck**: for every path the investigation listed for this
  story, what changed between the investigation commit and the current base
  (`git log --oneline <investigation-sha>..origin/main -- <paths>`), and
  whether any new call site appeared. "No changes" needs the command that
  showed it.
- **Departures from the feature design**: anything this plan does differently
  from the approved feature plan, or "None". A departure needs the owner's
  approval before implementation, and it triggers the adversarial challenge
  unless the owner waives it for this story.

### 2. Plan review, and challenge when required

The reviewer reviews the story plan under the Agent Table rules. The
challenger runs when the recorded policy requires it, when there is a
departure, or when the story touches security, permissions, or data-loss
surfaces and the policy says so. Findings loop back to the implementer.

### 3. Implement

The implementer implements the whole approved story plan in one pass, in a
dedicated worktree and branch, then verifies it locally:

- regression tests are shown to fail on the base before the fix
- tests and manual checks run against the local database and Azure Storage
  (Azurite), never QA or a shared environment
- third-party calls use a sandbox or test account where one exists

It hands off once, with the exact candidate commit, not after each file.

### 4. Code review and QA

The reviewer reviews the exact candidate commit against the approved story
plan and the story's acceptance criteria, with an approval receipt. Fixes loop
back through the implementer and return to code review. When the owner assigns
a QA seat, QA runs after code approval; a failure returns to the implementer
and then to code review.

### 5. Pull request

The implementer opens the pull request through the team's normal process:
branch naming, PR template, required checks, and reviewers. Do not merge
unless the owner says so. A merge is never a production deploy or a content
release.

## Completion

The table completes when the pull request is open (or merged, if the owner
asked). The final handoff gives the owner:

- the pull request link and the exact commit
- a one-line status update to paste into the tracker
- any follow-up the feature plan needs (a discovered requirement, a changed
  assumption), which goes back to the owner rather than into this story

Then clean up the worktree per `AGENTS.md`.

## Starting it

```text
/story-delivery <story file path>. Implementer: this session.
Reviewer: <session name>. Challenger: <session name, or none>.
```

In Codex, invoke the `story-delivery` skill with the same information.
