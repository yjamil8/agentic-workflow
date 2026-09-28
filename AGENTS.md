# AGENTS.md

## What This Repo Is

A portable multi-agent engineering toolkit: a durable file-based
collaboration protocol for coordinating separate Claude Code / Codex
sessions on one goal (Rally + the Agent Table), a required independent
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
AGENTS.md                              <- this file
CLAUDE.md                              <- imports AGENTS.md (@AGENTS.md)
strategies/
  Agent_Table_Collaboration_Rules.md   <- the Agent Table protocol contract
  Agent_AdversarialPlanReviewer.md     <- the plan_challenger judgment contract
guides/
  implementation-planning-guide.md     <- how to write a strong plan
  implementation-plan-template.md      <- copy this to start a plan
agents/
  pr-review-specialist.md              <- Claude Code PR reviewer (GitHub MCP or gh)
commands/
  review.md                            <- lightweight solo-review checklist
claude_skills/
  rally/                               <- Rally, Claude Code transport
  adversarial-plan-review/             <- thin pointer to the Codex-canonical skill
codex_skills/
  rally/                               <- Rally, Codex transport
  adversarial-plan-review/             <- canonical adversarial-plan-review skill
  pr-review/                           <- Codex PR reviewer (gh CLI)
scripts/
  install-local.sh                     <- installs commands, skills, global instructions
  init-work-repo.sh                    <- prepares a work repo for tables and plans
  serve_implementation_plans.py        <- local plan viewer (port 8765)
  plan_renderer.py                     <- markdown -> styled HTML plan renderer
  list-stale-worktrees.sh              <- worktree cleanup audit
```

## Planning, Scope, And Review Discipline

Owner scope is binding. Agents must not remove, defer, split off, or weaken an owner-requested requirement because it looks difficult, costly, or inconvenient. The owner decides whether to reduce scope and pays for the effort. If an agent finds a concrete blocker or expects substantially more work, they must explain the evidence and options to the owner while continuing unaffected authorized work. Changing the requested scope requires the owner's explicit approval. Reviewers must flag any plan or implementation that omits an owner-requested requirement without that approval.

Deliver the smallest reliable change that satisfies the owner's goal and preserves existing users. Every added mechanism must justify its complexity; completeness of paperwork is not product progress. These rules do not waive security, data protection, migration validation, feature-flag wiring, or explicit production approval, and do not authorize resuming paused work.

1. **Inspect before planning.** Inspect the relevant code, contracts, tests, configuration, runbooks, and evidence. Name the concrete affected files, endpoints, schemas, and operational lanes in the plan. Do not substitute another agent's summary for inspection. Identify any inaccessible core surface and the affected decision; do not silently defer a core unknown to implementation.
2. **Require evidence for scope.** Each requirement must support a requested outcome, preserve actual existing behavior/data, or prevent a concrete reachable correctness, security, financial, or reliability failure. Cite its basis briefly. A prior plan calling something mandatory is not sufficient justification. Speculative future features and hypothetical unsupported states are not release gates.
3. **Inventory before compatibility engineering.** Establish the affected existing data, active clients, and supported writers before designing historical reconstruction or backfill. With an empty affected inventory, prefer a verified cutover and prevention of unsupported writes over a general compatibility framework. Recheck at cutover and stop the affected operation on unexpected data; never discard existing users, links, records, or progress because a different table is empty.
4. **Reuse before expanding.** Before adding a service, abstraction, migration framework, rollout mode, or approval mechanism, briefly explain why existing machinery cannot meet the requirement. Remove obsolete constraints before adding replacements. Do not turn feature work into a reporting redesign, dormant-surface retrofit, or platform project without owner-approved scope expansion.
5. **Plan around working journeys.** Prefer a few end-to-end milestones over a layer-by-layer waterfall. Do not freeze every future schema in the first phase. Planning is sufficient when outcomes, existing-user preservation, affected contracts, main risks, and executable acceptance tests are clear. Resolve ordinary internal implementation details through code and tests; reopen only genuinely affected contracts when evidence changes.
6. **Review necessity as well as correctness.** Reviewers must challenge unjustified scope and consider removing or simplifying the requirement behind a finding. Blocking findings need a concrete failure or violated requirement, affected users/invariants, and reproduction or traceable code/data evidence. A failure need not have occurred in production to matter. Style preferences and speculative hardening remain nonblocking; do not manufacture findings to fill a quota.
7. **Keep verification proportional.** When independent review is requested, use one review per meaningful checkpoint, with focused re-review and affected tests after fixes. Retain exact reviewed source identities and run comprehensive integration tests at meaningful integration checkpoints. Do not invalidate unrelated evidence after bookkeeping-only changes, require separate agent reviews of approval-record commits, or create recursive approval chains. Recheck documentation/configuration changes that actually alter behavior or authority. Existing explicit owner checkpoints require owner resolution before being changed, not silent bypass.
8. **Expose cost and stop scope creep.** State a rough effort expectation for substantial work. If scope or elapsed effort materially exceeds it, promptly explain the expansion, actual user-visible progress, and recommended cuts. Seek approval for material expansion or new authority, not routine in-scope engineering decisions. Continue unaffected authorized work unless paused. Do not add another audit, amendment, or automation layer merely to manage the overhead of earlier ones.

## Multi-Agent Collaboration Protocol

When more than one agent session is working the same goal, use the Agent
Table protocol instead of the owner relaying messages between chats:

- [Agent_Table_Collaboration_Rules.md](strategies/Agent_Table_Collaboration_Rules.md)
  is the full contract: seats, turn rules, approval receipts, the UI
  presentation approval gate, and failure/recovery handling.
- Claude Code sessions use [`/rally`](claude_skills/rally/rally.md); Codex
  sessions use [`$rally`](codex_skills/rally/SKILL.md). Same `TABLE.md`
  format, interoperable, different transport per harness.
- Every implementation plan requires an independent adversarial plan
  challenge after ordinary plan approval and before implementation, unless
  the owner explicitly waives it in advance by saying `NO ADR` or `NO_ADR`.
  See [Agent_AdversarialPlanReviewer.md](strategies/Agent_AdversarialPlanReviewer.md)
  for the full judgment contract, and the `adversarial-plan-review` skill
  (canonical at [codex_skills/adversarial-plan-review/SKILL.md](codex_skills/adversarial-plan-review/SKILL.md),
  thin pointer for Claude at [claude_skills/adversarial-plan-review/command.md](claude_skills/adversarial-plan-review/command.md))
  for how to run it. The `plan_challenger` must be a different session from
  both the planner and the ordinary plan reviewer.
- A solo, low-stakes change that does not warrant a written plan needs no
  table and no adversarial review. The machinery exists for coordinated
  multi-agent work and consequential plans, not every edit. Once a written
  implementation plan exists, the challenge gate applies unless waived.

## PR / Code Review

- Claude Code: the `pr-review-specialist` subagent
  ([agents/pr-review-specialist.md](agents/pr-review-specialist.md)) does
  thorough line-by-line GitHub PR review via GitHub MCP tools, with a
  BLOCKER/MAJOR/MINOR/NIT severity taxonomy and inline suggestion blocks.
- Codex: the `pr-review` skill
  ([codex_skills/pr-review/SKILL.md](codex_skills/pr-review/SKILL.md)) does
  the same review, same priorities and severity taxonomy, via the `gh` CLI
  instead of an MCP server.
- For a lightweight solo review of uncommitted local changes with no PR
  involved, use [commands/review.md](commands/review.md) instead.
- Neither review agent commits, pushes, or merges. They only comment/review.

## Collaboration Rules

- Assume other agents may be working in these repos at the same time. Most parallel work will touch different files, but agents should not be surprised by unrelated code changes appearing in the worktree. Continue working with the current tree, avoid reverting changes you did not make, and only pause to ask if parallel edits directly conflict with the task at hand.
- Never push directly to `main` in a repo that requires review, including this one once it has collaborators. Changes intended for `main` must be pushed to a non-`main` branch, opened as a pull request, allowed to complete the repository's required checks, and merged through that pull request. A user request to commit, push, or merge work does not waive this required path. Adapt this to your own project's actual branch-protection policy; a solo, unprotected personal repo may reasonably relax it, but say so explicitly rather than assuming.
- Branch-creating or commit-intended-for-review work in a repo defaults to a dedicated worktree, not the primary checkout. The primary checkout is shared across concurrent sessions that rely on it staying on a stable ref, normally `main`; branching or committing there risks discarding another session's uncommitted work the moment anyone switches or resets it. Create the worktree under `<repo>-worktrees/<short-task-name>-<date>` and give the branch a name that cannot collide with a concurrent session's branch (see the branch naming rule below). Work directly in the primary checkout only for read-only inspection, or when the owner explicitly asks for that specific exception.
- When the owner says `merge`, it means complete the full remote integration workflow: create or update a compliant non-`main` branch, push it, open the pull request, satisfy the repository's required checks, merge the pull request into `origin/main`, then fetch and make the local `main` branch reference and any worktree where `main` is checked out match the exact `origin/main` tip. If local `main` cannot fast-forward because it contains local commits, first prove that each commit was integrated remotely, including by squash through an exact merged pull request or patch-equivalence check, or preserve genuinely unique commits on a named backup branch. Then synchronize local `main`. Do not treat a local merge, local commit on `main`, branch push, or open pull request as completion. Do not leave local `main` ahead of, behind, or diverged from `origin/main`. If a required check or repository rule blocks the merge, report that exact blocker and keep working on any in-scope fix that can resolve it. This authorization to merge code does not authorize a production deployment.
- After a pull request is merged and the primary local `main` worktree is synchronized, remove the completed task's secondary worktrees in the same session. Apply this to root and any nested repositories, remove registered nested worktrees before their parent worktree, and run `git worktree prune` in each owning repository. Do not leave merged worktrees or their duplicated build caches and dependencies consuming disk merely for convenience. Use [scripts/list-stale-worktrees.sh](scripts/list-stale-worktrees.sh) (configure `WORKTREE_REPOS` for your workspace) to confirm this happened; it reports which registered worktrees are already merged and clean, so cleanup compliance does not depend solely on the merging agent remembering the checklist below.
- Remove agent-created temporary worktrees, caches, and build outputs when their work is safely integrated or otherwise preserved. Do not delete `node_modules`, source-controlled files, another agent's artifacts, or broad directories as cleanup. If your stack has an expensive build/test cache (e.g. an Angular `.angular/cache`, a language toolchain's incremental-build cache), record its size before and after non-trivial work and clean it when it exceeds a threshold appropriate to your disk budget; first verify no other process is using that same cache before touching it. Final handoffs must state cache disposition and any deferred cleanup, in addition to worktree-removal evidence.
- Prevent work loss before every worktree removal. Fetch current `origin/main`, prove that the worktree commit is contained in `origin/main` or identify the exact merged pull request, run `git status --short --untracked-files=all` in the worktree and every nested repository, and inspect ignored files with `git clean -ndX`. Treat only recognized, regenerable caches and build outputs as disposable. If tracked changes, staged changes, untracked files, nested-repository changes, or unknown ignored files exist, do not remove the worktree. Preserve the work on a named branch and commit or in an explicit backup, and report what was preserved. Use the owning repository's `git worktree remove`; use `--force` only after these checks prove that every remaining ignored file is disposable.
- A worktree can be safe to lose and still be unsafe to remove: the work-loss checks prove nothing needs its *contents*, not that nothing needs its *path*. Before removing one, grep the workspace for inbound references to its location, because relative project references that climb above a worktree root resolve against its parent directory. If your workspace has a shared dependency checked out as its own worktree that other worktrees build through via a relative path, name it here explicitly, because removing it yields stale artifacts and tests that pass against uncompiled code.
- Before making, reviewing, committing, staging, or pushing changes in any repo or nested repo, verify the branch/base is current enough for the requested work. Run `git status --short --branch`, `git fetch origin main --prune`, and `git rev-list --left-right --count HEAD...origin/main` unless the user explicitly asked to work from another base. If the repo is detached, behind `origin/main`, or diverged, preserve local work on a named branch and commit, or in an explicit patch/backup when a commit cannot be made, then switch or create a real feature branch from current `origin/main`, reapply the work, and rerun the relevant build/tests before claiming push readiness.
- Never create agent work branches that could collide with a peer session's branch name. Follow your team's branch naming convention when it has one; otherwise agent-created continuation branches should include the repo name and date, for example `next-<repo-name>-<date>`. If the dated branch already exists, append a numeric suffix in order.
- Do not classify dirty files as unmerged local work until comparing them against current `origin/main`. Files that match `origin/main` are stale-base noise, not pending work.
- When the user asks to review repo changes for push, review all local changes in that repo, including staged, unstaged, untracked, conflicted, submodule, generated, and unrelated-looking changes. Call out anything that should not be pushed instead of narrowing the review to the presumed task.
- Before any commit/push readiness review, compare local diffs against `origin/main`, not only against `HEAD`, so already-merged work from a stale base is not misreported or recommitted.
- If a nested-repo path appears modified in a root/workspace repo, first determine whether it is just a submodule/gitlink pointer change or a dirty nested worktree. Stage the pointer only when it is clearly part of the requested deploy/pin update; otherwise call it out and leave it alone. Work inside nested repos only when the user explicitly asks to work in that nested repo.
- Before creating or switching branches, verify local work will not be dropped, hidden, overwritten, or stranded. If there is any risk to existing local changes, stop and tell the user before proceeding.
- After pushing a branch, provide the PR link when the remote returns one. If the owner requested only a push or PR, stop at that requested boundary. If the owner requested a merge, complete the full remote merge and local `main` synchronization workflow above without asking the owner to confirm the merge.

## Environments And Data Access

- **No production data access.** Agents cannot read the production database
  or storage. Never assume, request, or plan around production reads. When a
  decision depends on production data, say so explicitly, state what the
  available evidence cannot prove, and either design for the unknown or name
  the person who can run the check and the exact read-only query to give them.
- **QA database, read-only.** Use it for inventory, shape checks, and dated
  counts. Label QA counts as QA; they are evidence of shape, not of production
  volume. Never write to QA from an agent session.
- **Local database and Azure Storage.** Development and tests run against a
  local database and local Azure Storage (the Azurite emulator, or a personal
  development storage account). They must be set up before implementation or
  QA starts; a plan whose verification needs them names the setup. Tests must
  never point at QA or any shared environment.
- **Content releases ship through GitHub Actions.** Content and data changes
  that production needs go through the team's GitHub Actions release
  workflow, separate from the application deploy. Never hand-apply content to
  a shared environment, and never treat an application deploy as a content
  release.
- **Third-party services.** Changes that call or configure third-party
  services name the service, the credentials' location (never in code, plans,
  or logs), and how to undo the change on the service's side.

## Feature Flag Wiring Discipline

When adding, renaming, deleting, defaulting, or relying on any feature flag, agents must prove the full production wiring in the same change/review. Do not stop at local/dev config.

For each affected surface, prove the flag is actually wired end to end, not just declared:

- typed options/config classes or their equivalent
- environment/config defaults for every deployment target (local, staging, production)
- build-time generation scripts and Docker/CI build args, if the flag is baked in at build time
- deployment workflow env rendering when the flag is externally configurable
- env examples and boolean validation when applicable
- deploy/service-targeting tests that prevent future drift

For cross-service features, prove both sides are enabled or intentionally disabled together. If a flag affects user-facing behavior, explicitly state whether it is compile-time, runtime, or both, and whether the currently deployed production build already contains it. Treat a missing build/deploy/env mapping as a bug, not a follow-up.

Production/local parity is mandatory for enabled behavior. If a user-facing or runtime-affecting feature flag is enabled in production, the normal local development lane must enable the same behavior and agents must test it locally before claiming the feature is done, push-ready, or production-safe. Do not allow production-only enablement with local default-off behavior unless the user explicitly approves a temporary exception in the current conversation and the exception is documented with an alternate prod-like local test lane. Treat silent production/local feature drift as a severe process failure because it invalidates local QA.

Every new feature flag must be enabled in the normal local development lane while the feature is being built and reviewed, unless the user explicitly approves a temporary exception in the current conversation. A feature flag that is off locally by default cannot prove the feature works, cannot support browser QA, and must not be treated as complete.

## UI Quality Discipline

- Ensure icons are centered. Check icon-only buttons, chips, pills, cards, nav items, empty states, and CTA rows for true horizontal and vertical centering before handing off.
- If icons sit next to text, verify the icon and text are vertically aligned, use appropriate `inline-flex`/`flex` alignment, and are not separated by excessive gaps. Do not assume icon components or SVGs are aligned by default.
- Before finalizing UI changes, explicitly scan the touched components for off-center icons, text-adjacent icons that sit too high/low, and icon/text spacing that looks accidental on desktop and mobile.

## Source-Of-Truth Fix Discipline

- Do not hide invalid backend/domain state with frontend filters, suppression, or display-only guards. If user state, tasks, results, permissions, onboarding, or progression data is wrong, fix the source-of-truth logic that created or returned the bad state.
- Frontend guards are acceptable for defensive rendering, permissions display, loading/null handling, and graceful empty states, but they must not be the primary fix for impossible domain states. Frontend filtering that hides invalid business state is code bloat/poison unless it is paired with a backend invariant fix, data cleanup, and regression coverage.
- When a bug appears in user-facing state, first identify whether the bad data should exist at all. If not, prevent creation, repair existing state through the proper backend/data lane, and add regression tests or health checks so the issue cannot resurface later through another UI surface.

## Test Double And Fixture Fidelity

- A double or fixture that does not behave like the real thing certifies defects rather than catching them. Match the behaviour that matters: replay semantics, emission timing, nullability, error shape.
- A fixture must never substitute a silent default for an input it does not recognise. Throw and name the missing input.
- Before asserting on how a component reacts to a dependency, confirm the double can express the behaviour under test.
- When a suite passes, ask what the doubles are hiding. A test double has often hidden more defects than the production code contained.

## Absolute Claims To Users Must Be Traced

- Any user-facing claim that something is impossible, permanent or gone must be traced to the code enforcing it before it ships. Covers never, cannot, will not, no longer, gone, last chance.
- Cite the setting, expiry, retention job or branch in the review. Untraced means it does not ship.
- When replacing a false absolute, do not substitute another. State what is true.
- Prefer a claim about what the product will do ("the last email we will send") over what can exist ("cannot be reissued"). The first is a schedule you control.

## Product-Rule Provenance Discipline

- Existing product behavior must be traced to inspected code, tests, an established active runbook, or an explicit owner decision.
- An implementation plan may restate an existing rule only with concrete provenance. A plan is not independently authoritative merely because it labels something required or locked.
- Any behavior without authoritative provenance must be labeled as a proposal or `owner decision required`. It must not be used as an implementation constraint, audit criterion, canary rejection reason, or completion gate.
- External provider conventions, competitor behavior, and generic best practices may inform proposals, but must never implicitly override this product's actual established behavior.
- When a plan conflicts with code, tests, an active runbook, or an owner decision, resolve the substantive conflict before proceeding with the affected work. Continue unrelated authorized work unless the owner has paused it; do not turn a bounded conflict into a project-wide stop or invent a new product rule to avoid clarification.

## Heuristic Discipline

- Do not add rigid, product-specific, or keyword-list heuristics unless the user explicitly approves them. Prefer generic metadata-driven contracts, compact prompts, and auditable model outputs over brittle rule piles, especially in a multi-tenant or multi-domain system.
- Avoid prompt/code bloat. Before adding constraints, remove obsolete ones and make the smallest reusable change that solves the observed failure.
- When updating prompts, revise the prompt as a whole rather than appending isolated fixes. Reflect validated experiment learnings by preserving useful constraints, removing stale or contradictory language, and adding only measured reusable instructions that directly address observed failures.

## Punctuation Discipline

- Never use em dashes (Unicode U+2014) anywhere, including UI copy, prompts, documentation, tests, code comments, or agent-authored text. Use a hyphen or rewrite the sentence.

## Runbooks

- No runbooks exist yet. Do not assume one exists, search for one, or treat a missing runbook as a blocker; inspect the code, configuration, and pipeline definitions (for example the GitHub Actions workflows) directly.
- When the owner and agents repeat a procedure (a content release, local database and Azurite setup, a QA read query, a third-party change), propose a runbook for it. Create it only when the owner agrees, at `<work-repo-root>/runbooks/<topic>.md`, which `scripts/init-work-repo.sh` keeps out of team commits like `agent_tables/`.
- A runbook must be correct, complete, and runnable by someone new, and kept current when the procedure changes. It is not scratch notes or a partial plan.

## Implementation Plans

Keep exactly one canonical plan file per workstream in the work repo, at
`<work-repo-root>/implementation_plans/MMDDYY/<slug>-plan-YYYYMMDD.md`, linked
from the workstream's Agent Table and updated in place (never a new file per
version). Start from
[guides/implementation-plan-template.md](guides/implementation-plan-template.md)
and follow [guides/implementation-planning-guide.md](guides/implementation-planning-guide.md).
Versioning, review rounds, and the UI presentation gate are defined in
[Agent_Table_Collaboration_Rules.md](strategies/Agent_Table_Collaboration_Rules.md).

Run the local plan viewer from the work repo's root:

```bash
python3 <agentic-workflow-root>/scripts/serve_implementation_plans.py   # http://127.0.0.1:8765/plans
# or from anywhere:
python3 <agentic-workflow-root>/scripts/serve_implementation_plans.py --plans-dir <work-repo-root>/implementation_plans
```

When citing a plan in a table entry, handoff, or message to the owner, link
both the viewer URL (`http://127.0.0.1:8765/plan/<path-relative-to-implementation_plans>`)
and the repo-relative `.md` source path. The viewer is a formatted reading
view and the `.md` file is the exact reviewed source; neither replaces the
other. Confirm the URL resolves before sending it
(`curl -s -o /dev/null -w '%{http_code}' <url>`); if the server is not
running, start it or say so instead of handing over a dead link.
