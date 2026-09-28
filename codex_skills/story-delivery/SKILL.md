---
name: story-delivery
description: Take one user story from story plan through review, implementation, code review, and pull request, through an Agent Table with an implementer, a reviewer, and an optional adversarial challenger. Use when the owner hands over a story file or story text to implement. Not for designing a whole feature (use feature-discovery).
---

# Story Delivery

Announce that this skill is in use, then:

1. Read the applicable `AGENTS.md`, then read in full:
   - `<agentic-workflow-root>/strategies/Workflow_Story_Delivery.md` (this workflow's contract; it controls the loop and gates)
   - `<agentic-workflow-root>/strategies/Agent_Table_Collaboration_Rules.md`
   - `<agentic-workflow-root>/strategies/Agent_AdversarialPlanReviewer.md` if you hold the `plan_challenger` seat
2. Use the installed `rally` skill for table creation, joining, turns, handoffs, and notification. Use one table per story.
3. Make sure the work repository has been prepared (`<agentic-workflow-root>/scripts/init-work-repo.sh <work-repo>`).
4. On create, record the story, its feature plan and investigation commits when it came from Feature Discovery, and the challenge policy (inherited from the feature table unless the owner states otherwise; ask for a standalone story). Never infer a `NO ADR` waiver.
5. Write the story plan from `<agentic-workflow-root>/guides/story-plan-template.md`, including the inventory recheck and any departures from the feature design.
6. Implement only after the story plan is approved (and challenged when required), in a dedicated worktree, against the local database and Azure Storage (Azurite). Open the pull request through the team's process; merge only if the owner says so.
