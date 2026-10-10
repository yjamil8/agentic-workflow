# Workspace operations

Read the sections that the [AGENTS.md](../AGENTS.md) routing table selects
before the affected work. A section is not authority to start an operation.
Paths written as `<agentic-workflow-root>` mean the toolkit checkout; this file
is read from the checkout, not installed, so the placeholder is not rendered.

## Collaboration Rules

- Assume other agents may be working in these repos at the same time. Most parallel work will touch different files, but agents should not be surprised by unrelated code changes appearing in the worktree. Continue working with the current tree, avoid reverting changes you did not make, and only pause to ask if parallel edits directly conflict with the task at hand.
- Never push directly to `main` in a repo that requires review, including this one once it has collaborators. Changes intended for `main` must be pushed to a non-`main` branch, opened as a pull request, allowed to complete the repository's required checks, and merged through that pull request. A user request to commit, push, or merge work does not waive this required path. Adapt this to your own project's actual branch-protection policy; a solo, unprotected personal repo may reasonably relax it, but say so explicitly rather than assuming.
- Branch-creating or commit-intended-for-review work in a repo defaults to a dedicated worktree, not the primary checkout. The primary checkout is shared across concurrent sessions that rely on it staying on a stable ref, normally `main`; branching or committing there risks discarding another session's uncommitted work the moment anyone switches or resets it. Create the worktree under `<repo>-worktrees/<short-task-name>-<date>` and give the branch a name that cannot collide with a concurrent session's branch (see the branch naming rule below). Work directly in the primary checkout only for read-only inspection, or when the owner explicitly asks for that specific exception.
- When the owner says `merge`, it means complete the full remote integration workflow: create or update a compliant non-`main` branch, push it, open the pull request, satisfy the repository's required checks, merge the pull request into `origin/main`, then fetch and make the local `main` branch reference and any worktree where `main` is checked out match the exact `origin/main` tip. If local `main` cannot fast-forward because it contains local commits, first prove that each commit was integrated remotely, including by squash through an exact merged pull request or patch-equivalence check, or preserve genuinely unique commits on a named backup branch. Then synchronize local `main`. Do not treat a local merge, local commit on `main`, branch push, or open pull request as completion. Do not leave local `main` ahead of, behind, or diverged from `origin/main`. If a required check or repository rule blocks the merge, report that exact blocker and keep working on any in-scope fix that can resolve it. This authorization to merge code does not authorize a production deployment.
- After a pull request is merged and the primary local `main` worktree is synchronized, remove the completed task's secondary worktrees in the same session. Apply this to root and any nested repositories, remove registered nested worktrees before their parent worktree, and run `git worktree prune` in each owning repository. Do not leave merged worktrees or their duplicated build caches and dependencies consuming disk merely for convenience. Use [scripts/list-stale-worktrees.sh](../scripts/list-stale-worktrees.sh) (configure `WORKTREE_REPOS` for your workspace) to confirm this happened; it reports which registered worktrees are already merged and clean, so cleanup compliance does not depend solely on the merging agent remembering the checklist below.
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
- **Protect your local working data.** Your local database and local Azure
  Storage hold your working state. No agent may drop, recreate, clean-restore,
  truncate, or wipe them without explicit owner approval in the current
  conversation for that exact operation. This rule comes from a real incident
  in which a test switched its host to a development environment, fell through
  to the working connection string, and its database reset replaced the whole
  working database.
  - Tests use their own throwaway database and storage container (or an
    in-memory provider), never the working ones. Never point a test host at a
    development configuration that can resolve to the working connection.
  - Before running anything that creates, drops, cleans, seeds, or resets a
    database or storage container, prove which one it will connect to. A
    passing test proves nothing about what it deleted.
  - Restores and experiments go into a new, uniquely named database. Replace
    the working database only by a rename swap with owner approval, keeping
    the old one.
  - Take a backup before any owner-approved destructive operation. If a guard
    or safety check refuses an operation, stop and report; never work around it.
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

## Runbooks

- No runbooks exist yet. Do not assume one exists, search for one, or treat a missing runbook as a blocker; inspect the code, configuration, and pipeline definitions (for example the GitHub Actions workflows) directly.
- When the owner and agents repeat a procedure (a content release, local database and Azurite setup, a QA read query, a third-party change), propose a runbook for it. Create it only when the owner agrees, at `<work-repo-root>/runbooks/<topic>.md`, which `scripts/init-work-repo.sh` keeps out of team commits like `agent_tables/`.
- A runbook must be correct, complete, and runnable by someone new, and kept current when the procedure changes. It is not scratch notes or a partial plan.

## Implementation Plans

Keep exactly one canonical plan file per workstream in the work repo, at
`<work-repo-root>/implementation_plans/MMDDYY/<slug>-plan-YYYYMMDD.md`, linked
from the workstream's Agent Table and updated in place (never a new file per
version). Start from
[guides/implementation-plan-template.md](../guides/implementation-plan-template.md)
and follow [guides/implementation-planning-guide.md](../guides/implementation-planning-guide.md).
Versioning, review rounds, and the UI presentation gate are defined in
[Agent_Table_Collaboration_Rules.md](Agent_Table_Collaboration_Rules.md).

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
