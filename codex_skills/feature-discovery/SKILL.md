---
name: feature-discovery
description: Turn a feature request into an approved investigation, proposal, feature plan, and paste-ready user stories, through an Agent Table with a planner, a reviewer, and an optional adversarial challenger. Use when the owner asks to plan, investigate, or break down a feature before any implementation. Produces no code. Not for implementing a single story (use story-delivery).
---

# Feature Discovery

Announce that this skill is in use, then:

1. Read the applicable `AGENTS.md`, then read in full:
   - `<agentic-workflow-root>/strategies/Workflow_Feature_Discovery.md` (this workflow's contract; it controls the stages and gates)
   - `<agentic-workflow-root>/strategies/Agent_Table_Collaboration_Rules.md`
   - `<agentic-workflow-root>/strategies/Agent_AdversarialPlanReviewer.md` if you hold the `plan_challenger` seat
2. Use the installed `agent-table` skill for table creation, joining, turns, handoffs, and notification. This skill does not replace agent-table transport.
3. Make sure the work repository has been prepared (`<agentic-workflow-root>/scripts/init-work-repo.sh <work-repo>`); tables and artifacts live only in its excluded `agent_tables/` and `implementation_plans/` folders.
4. On create, ask the owner for any missing part of the owner policy (goal and scope, which stages are challenged, the default story challenge policy) and record it verbatim before investigating. Never infer a `NO ADR` waiver.
5. Build each artifact from its template:
   - investigation: `<agentic-workflow-root>/guides/feature-investigation-template.md`
   - proposal: `<agentic-workflow-root>/guides/feature-proposal-template.md`
   - feature plan: `<agentic-workflow-root>/guides/implementation-plan-template.md`, following `<agentic-workflow-root>/guides/implementation-planning-guide.md`
   - stories: `<agentic-workflow-root>/guides/user-story-template.md`
6. Do not start the feature plan until the owner has chosen a proposal option, and do not start implementation in this table.
