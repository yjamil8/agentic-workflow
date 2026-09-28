# Workflow: Feature Discovery

Turns a feature request into an approved design and a set of user stories
ready to paste into the team tracker. It produces no code. Implementation
happens later, one story at a time, through
[Workflow_Story_Delivery.md](Workflow_Story_Delivery.md).

This workflow runs on the Agent Table protocol
([Agent_Table_Collaboration_Rules.md](Agent_Table_Collaboration_Rules.md)) and
Rally transport. Those rules still govern turns, handoffs, immutable dated
reviews, approval receipts, and owner decisions; this document adds the
stages, artifacts, and gates specific to feature discovery.

## Seats

| Seat | Role name in Rally | Does |
|---|---|---|
| Planner | `planner` | Investigates, writes the proposal, feature plan, and stories. |
| Reviewer | `reviewer` | Reviews each stage artifact; never the author. |
| Challenger | `plan_challenger` | Runs the adversarial review at the stages the owner selected. A different session from all others. |
| Co-planner (optional) | `co_planner` | Develops the investigation, options, or strategy with the planner under [Agent_CoPlanner.md](Agent_CoPlanner.md). Adds no approval gate. |

The planner and reviewer must be different sessions. The challenger seat is
needed only if the owner selects at least one challenged stage. A co-planner is
worth adding for a large feature whose investigation spans several services; it
counts as a co-author, so it cannot also review or challenge the same work.

## Artifacts

All artifacts live in the work repository, in the locally excluded folders set
up by `scripts/init-work-repo.sh`. None of them are committed to the team
repository or to this toolkit.

```text
<work-repo>/implementation_plans/MMDDYY/<feature-slug>/
  investigation.md          (from guides/feature-investigation-template.md)
  proposal.md               (from guides/feature-proposal-template.md)
  feature-plan.md           (from guides/implementation-plan-template.md)
  stories/
    S01-<story-slug>.md     (from guides/user-story-template.md)
    S02-<story-slug>.md
<work-repo>/agent_tables/<feature-slug>/
  TABLE.md
  reviews/
  decisions/
```

Each artifact is versioned in place (`v1`, `v2`, ...) with a revision history,
exactly as implementation plans are.

## Setup: record the owner's policy first

Before any investigation, the creating session asks the owner for, and records
verbatim in a `## Owner policy` section of `TABLE.md` (outside the Rally
managed block):

1. **Goal and scope** of the feature, and anything explicitly excluded.
2. **Challenge policy for this feature**: which of `investigation`,
   `proposal`, and `feature plan` get an adversarial review. Every stage the
   owner does not select is recorded as the owner's advance `NO ADR` waiver for
   that stage. Never infer the policy; if the owner has not stated it, ask.
3. **Default challenge policy for this feature's stories**, for example "no
   challenge unless a story departs from the approved design or touches
   security or data-loss surfaces". Story tables inherit it.

## Stages

Each stage ends with a review. A stage selected for challenge then goes to the
challenger before the next stage starts. Findings return to the planner, who
revises the same artifact to the next version; the reviewer re-reviews the
change, and the challenger re-checks its own findings.

### Stage 1: Investigation

The planner writes `investigation.md`: every call site, entry point, reader
and writer of affected data, contract, configuration and flag, third-party
touchpoint, and user-facing surface, with the exact search commands, their
counts, and the commit each repository was at. It records the data shape from
the QA database (read-only, labeled as QA), existing mechanisms that could be
reused, invariants discovered, and unknowns, including anything only
production data could answer and who could check it.

The reviewer checks **completeness first**: re-run a sample of the searches,
look for call sites the searches would miss (reflection, configuration,
string-based dispatch, other repositories, scheduled jobs, pipelines), and
confirm each "not affected" claim is traced. Incomplete inventory is the most
common reason a plan fails review; it is far cheaper to catch here.

### Stage 2: Proposal

The planner writes `proposal.md`: the problem and outcome, constraints taken
from the investigation, two to four real options (always including the
smallest change that could work), a comparison, a recommendation, and the
owner decisions required.

The reviewer checks that each option is real and fairly costed, that the
recommendation follows from the evidence, and that every claim traces to the
investigation. After review (and challenge, if selected), **the owner chooses
the option.** Record the choice in `decisions/` before the feature plan
starts. The planner does not start the plan on an unchosen option.

### Stage 3: Feature plan

The planner writes `feature-plan.md` from the implementation plan template,
for the chosen option. Its milestones are the candidate stories: each one a
journey that can be demonstrated on its own and shipped as one reviewable pull
request. The plan links the investigation and proposal versions it builds on.

The reviewer reviews it as an ordinary implementation plan under the Agent
Table rules, including the UI presentation gate when anything user-visible
changes.

### Stage 4: Stories

The planner writes one file per story from the user story template. The
reviewer checks:

- **Coverage**: every requirement in the feature plan maps to at least one
  story, and no story adds scope the plan does not contain. Include the
  requirement-to-story map in the review artifact.
- **Independence**: each story can be implemented, reviewed, and merged on
  its own, with dependencies stated explicitly and ordered.
- **Testability**: every acceptance criterion is a concrete, checkable
  scenario.
- **Paste safety**: the pasteable part of each story is self-contained and
  free of private paths, table or seat names, review IDs, and other agent
  process language. Traceability to private artifacts lives only in the
  story's "do not paste" section.

## Completion

The table completes when the stories are approved. The final handoff gives the
owner:

- the list of story files in dependency order, ready to paste
- the approved versions and commits of the investigation, proposal, and
  feature plan, which story tables will cite
- the recorded story challenge policy

Pasting the stories into the tracker is the owner's step. Implementation of
each story starts a separate Story Delivery table.

## Starting it

```text
/feature-discovery <feature name>: <goal>. Planner: this session.
Reviewer: <session name>. Challenger: <session name, or none>.
```

In Codex, invoke the `feature-discovery` skill with the same information. The
creating session then asks for any part of the owner policy that is missing.
