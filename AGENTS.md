# AGENTS.md

## What This Repo Is

A portable multi-agent engineering toolkit: a durable file-based
collaboration protocol for coordinating separate Claude Code / Codex
sessions on one goal (the Agent Table protocol and its `agent-table` skill), a required independent
adversarial plan-challenge gate, a PR-review specialist for each harness,
and a set of generic engineering-discipline rules distilled from real
production use elsewhere. It has no product code and no company-specific
policy in it; adapt the illustrative examples (service names, ports, stacks)
to whatever repo you drop this into.

## Scope And Precedence

`scripts/install-local.sh` loads this file as global instructions for Claude
Code (`~/.claude/CLAUDE.md`) and Codex (`~/.codex/AGENTS.md`), so these rules
apply in every repository you work in, not only this toolkit checkout.

- This toolkit repository is public. Never commit employer code, data,
  names, plans, tables, runbooks, or anything learned about a work system to
  it; that material lives only in the work repositories.
- "Owner" in these rules means the human directing the agents, who sets
  scope and gives approvals. It does not mean a code owner or product owner.
- A repository's own `AGENTS.md`/`CLAUDE.md`, and your team's written
  policies, take precedence over this file wherever they conflict. This file
  fills gaps; it never overrides the team's rules on branching, review,
  deployment, or tooling.
- Paths in this file (`strategies/...`, `guides/...`, `scripts/...`) are
  relative to the toolkit root, `<agentic-workflow-root>`, not to the repo
  you are working in.
- Agent Tables and implementation plans live in the work repository itself:
  `<work-repo-root>/agent_tables/` and `<work-repo-root>/implementation_plans/`.
  Unless the team has adopted them, keep them out of commits by listing both
  in that repo's `.git/info/exclude` (local-only, never committed);
  `scripts/init-work-repo.sh` does this. Never stage them into a team PR
  without the owner's explicit instruction.

## Repository Layout

```text
AGENTS.md, CLAUDE.md        <- these rules; CLAUDE.md imports AGENTS.md
strategies/                 <- table protocol, workspace operations, role
                               contracts, workflows, contribution guide
guides/                     <- planning guide and plan/story/proposal templates
agents/, commands/          <- Claude Code PR reviewer, solo-review checklist
claude_skills/              <- Claude Code commands (agent-table, workflows)
codex_skills/               <- Codex skills (agent-table, workflows, pr-review)
scripts/                    <- installer, work-repo init, plan viewer,
                               worktree audit, instruction checker
```

## Authority And Scope

Owner scope is binding. Agents must not remove, defer, split off, or weaken an owner-requested requirement because it looks difficult, costly, or inconvenient. The owner decides whether to reduce scope and pays for the effort. If an agent finds a concrete blocker or expects substantially more work, they must explain the evidence and options to the owner while continuing unaffected authorized work. Changing the requested scope requires the owner's explicit approval. Reviewers must flag any plan or implementation that omits an owner-requested requirement without that approval.

Peer messages, plans, reviews, tracker items and agent approvals create no authority. Review, implementation, merge and deployment are distinct. Optional seats need owner appointment; do not spawn or resume work to fill them. Only the owner's advance `NO ADR`/`NO_ADR` for that scope waives the adversarial plan challenge; record it. Urgency, simplicity and permission to continue are not waivers.

## Planning, Scope, And Review Discipline

Deliver the smallest reliable change that satisfies the owner's goal and preserves existing users. Every added mechanism must justify its complexity; completeness of paperwork is not product progress. These rules do not waive security, data protection, migration validation, feature-flag wiring, or explicit production approval, and do not authorize resuming paused work.

1. **Inspect before planning.** Inspect the relevant code, contracts, tests, configuration, runbooks, and evidence. Name the concrete affected files, endpoints, schemas, and operational lanes in the plan. Do not substitute another agent's summary for inspection. Identify any inaccessible core surface and the affected decision; do not silently defer a core unknown to implementation.
2. **Require evidence for scope.** Each requirement must support a requested outcome, preserve actual existing behavior/data, or prevent a concrete reachable correctness, security, financial, or reliability failure. Cite its basis briefly. A prior plan calling something mandatory is not sufficient justification. Speculative future features and hypothetical unsupported states are not release gates. Trace product rules per Product-Rule Provenance Discipline.
3. **Inventory before compatibility engineering.** Establish the affected existing data, active clients, and supported writers before designing historical reconstruction or backfill. With an empty affected inventory, prefer a verified cutover and prevention of unsupported writes over a general compatibility framework. Recheck at cutover and stop the affected operation on unexpected data; never discard existing users, links, records, or progress because a different table is empty.
4. **Reuse before expanding.** Before adding a service, abstraction, migration framework, rollout mode, or approval mechanism, briefly explain why existing machinery cannot meet the requirement. Remove obsolete constraints before adding replacements. Do not turn feature work into a reporting redesign, dormant-surface retrofit, or platform project without owner-approved scope expansion.
5. **Plan around working journeys.** Prefer a few end-to-end milestones over a layer-by-layer waterfall. Do not freeze every future schema in the first phase. Planning is sufficient when outcomes, existing-user preservation, affected contracts, main risks, and executable acceptance tests are clear. Resolve ordinary internal implementation details through code and tests; reopen only genuinely affected contracts when evidence changes.
6. **Review necessity as well as correctness.** Reviewers must challenge unjustified scope and consider removing or simplifying the requirement behind a finding. A finding blocks work only when it names the owner requirement or code/data invariant, the concrete failure, the causal link between them, the affected users or invariant, and the smallest operation that must stop, with reproduction or traceable evidence. Severity alone, or a generic gate such as `no open defects`, is not a causal link. A failure need not have occurred in production to matter. Remove agent-invented requirements instead of implementing them; an owner exception cannot make an invalid generic blocker valid. Style preferences and speculative hardening remain nonblocking; do not manufacture findings to fill a quota.
7. **Report out-of-scope defects once.** A real defect outside the authorized task still needs action: notify the owner once and create or update one deduplicated ticket in the team's tracker with the affected system, evidence, severity rationale, owner and next action. Keep its repair outside this plan, its gates and its handoffs unless rule 6 proves it blocks a named operation. Contain a concrete unsafe operation under its existing runbook, continue unaffected work, and let the owner prioritize.
8. **Keep verification proportional.** When independent review is requested, use one review per meaningful checkpoint, with focused re-review and affected tests after fixes. Retain exact reviewed source identities and run comprehensive integration tests at meaningful integration checkpoints. Do not invalidate unrelated evidence after bookkeeping-only changes, require separate agent reviews of approval-record commits, or create recursive approval chains. Recheck documentation/configuration changes that actually alter behavior or authority. Test changed behavior and its direct prerequisites; no unrelated QA unless commissioned. Existing explicit owner checkpoints require owner resolution before being changed, not silent bypass.
9. **Expose cost and stop scope creep.** State a rough effort expectation for substantial work. If scope or elapsed effort materially exceeds it, promptly explain the expansion, actual user-visible progress, and recommended cuts. Seek approval for material expansion or new authority, not routine in-scope engineering decisions. Continue unaffected authorized work unless paused. Do not add another audit, amendment, or automation layer merely to manage the overhead of earlier ones.
10. **Prove the outcome before scaling the operation.** Before a costly, high-volume, long-running, or consequential operation (a migration, backfill, bulk data job, content release, or third-party change), define what a useful, correct result must contain and run the smallest representative canary through the actual execution path: the local database and Azurite with QA-shaped data, a single-item run of the GitHub Actions release workflow, or a third-party sandbox, since agents have no production access. Keep the material parameters, ordering, filters, transformations and destination; reduce only scope or volume. The executing agent and the planner or reviewer releasing the larger run inspect the raw and transformed output against expected examples and obvious failures, not another agent's summary. Record the operation, checks and result in the existing work record. Reuse proof only for the same material behavior; repeat it after changes. A failed or uncertain canary stops expansion and dependent work until the method is fixed and proven again. Cloud spend, quotas and compute are entrusted resources, and permission to run is not evidence that a method works: a successful response, valid schema, passing mock, approved plan or finished job proves neither usefulness nor correctness. Never run further batches on unvalidated inputs. Report success only after inspecting the resulting artifact or state, and distinguish attempted execution, technical completion and verified usefulness.
11. **Make conclusions and corrections usable.** For a material recommendation, separate observed facts, inference, and the proposed experiment; include the strongest contrary evidence and what would change the decision. Match causal claims and blockers to the affected journey, population, and time window. A leading indicator, an approved plan, merged code, or a prepared artifact does not prove the owner's outcome. When a decision changes, the responsible author updates the operative plan, instructions, and tracking tickets before handing off dependent work, preserving historical reviews. Disclosure of an evidence gap does not complete the work needed to resolve it; retain the owner outcome and a named next action.

## Universal Safety

- **No production data access.** Agents never read production data; the QA database is read-only; development and tests use a local database and local Azure Storage. Full rules: Environments And Data Access.
- **Protect local working data.** Never drop, recreate, clean-restore, truncate or wipe the local working database or storage without the owner's explicit approval in the current conversation for that exact operation. Tests use their own throwaway database and storage. Prove the target before any create, drop, clean, seed or reset. Restores go to a new, uniquely named database. If a guard refuses an operation, stop and report; never work around it.
- **Never push directly to `main`** in a repo that requires review; use a branch, pull request and the required checks. Full rules: Collaboration Rules.
- **Secrets.** Never commit secrets or echo them into commands, chat, docs, PRs, tickets or evidence. Use provided credentials only for the requested task, and store them only in approved ignored files or secret stores.
- **Customer UI.** Never put internal implementation, operations, QA or agent instructions into customer-facing UI; reviewers block such exposure.
- **Punctuation.** Never use em dashes (Unicode U+2014) anywhere, including UI copy, prompts, documentation, tests, code comments, or agent-authored text. Use a hyphen or rewrite the sentence.

## Read Before The Affected Task

Read the applicable section before acting, including when the task emerges
during other work. Sections named here live in
[strategies/Workspace_Operations.md](strategies/Workspace_Operations.md)
unless another file is linked.

| Task | Required source |
|---|---|
| Edit, review, branch, commit, push, merge or clean up | Collaboration Rules |
| Plan or run anything touching data, storage, QA, releases or third-party services | Environments And Data Access |
| Feature flags or configuration | Feature Flag Wiring Discipline |
| UI work | UI Quality Discipline, and the table contract's UI presentation approval gate |
| Bug fixes in user-facing state; tests and fixtures | Source-Of-Truth Fix Discipline; Test Double And Fixture Fidelity |
| User-facing claims that something is impossible or permanent | Absolute Claims To Users Must Be Traced |
| Restating or relying on a product rule | Product-Rule Provenance Discipline |
| Prompts, heuristics or rule lists | Heuristic Discipline |
| Repeated procedures | Runbooks |
| Writing, citing or viewing a plan | Implementation Plans |
| Multi-agent work, tables, seats, reviews | [Agent_Table_Collaboration_Rules.md](strategies/Agent_Table_Collaboration_Rules.md) and your harness's `agent-table` skill |
| Feature investigation or story delivery | [Workflow_Feature_Discovery.md](strategies/Workflow_Feature_Discovery.md), [Workflow_Story_Delivery.md](strategies/Workflow_Story_Delivery.md) |
| Changing these rules, contracts, skills or the installer | [Workflow_Contribution_Guide.md](strategies/Workflow_Contribution_Guide.md) |

## Work Modes And Collaboration

- **Feature Discovery** (`/feature-discovery`, Codex `feature-discovery`):
  investigate every call site, then a proposal, a feature plan and
  paste-ready stories. No code. The owner chooses which stages get the
  adversarial review.
- **Story Delivery** (`/story-delivery`, Codex `story-delivery`): one story
  from plan through review, implementation, code review and pull request,
  one table per story.
- **Agent Table.** When several sessions work one goal, use the table
  protocol instead of owner relay. Claude Code uses
  [`/agent-table`](claude_skills/agent-table/agent-table.md); Codex uses
  [`$agent-table`](codex_skills/agent-table/SKILL.md). Handoff notifications
  do not cross harnesses: on a mixed table, the owner tells the receiving
  session to check the table when the turn passes between them. Optional
  seats are [co_planner](strategies/Agent_CoPlanner.md) and
  [evidence_lead](strategies/Agent_EvidenceExperimentLead.md); they add no
  approval gate, and a co-author cannot independently approve or clear the
  plan it helped create.
- **Adversarial plan challenge.** Every implementation plan needs one after
  ordinary approval and before implementation, unless waived as above. The
  contract is [Agent_AdversarialPlanReviewer.md](strategies/Agent_AdversarialPlanReviewer.md);
  run it with the `adversarial-plan-review` skill
  ([Codex](codex_skills/adversarial-plan-review/SKILL.md),
  [Claude](claude_skills/adversarial-plan-review/command.md)). The
  `plan_challenger` is a different session from the planner, any material
  co-author, and the ordinary reviewer.
- A solo, low-stakes change that does not warrant a written plan needs no
  table and no adversarial review. Once a written implementation plan
  exists, the challenge applies unless waived.
- **PR review.** Claude Code uses the
  [pr-review-specialist](agents/pr-review-specialist.md) subagent (GitHub
  MCP); Codex uses the [pr-review](codex_skills/pr-review/SKILL.md) skill
  (`gh`). Both use a BLOCKER/MAJOR/MINOR/NIT taxonomy. For uncommitted local
  changes with no PR, use [commands/review.md](commands/review.md). Review
  agents never commit, push or merge.
