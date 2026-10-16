# agentic-workflow

A portable multi-agent engineering toolkit for Claude Code and Codex. It has no
product code and no company-specific policy; examples in the docs (service
names, ports, stacks) are illustrative.

Start with [AGENTS.md](AGENTS.md). It holds the engineering rules and the repo
layout. `CLAUDE.md` imports it, so Claude Code and Codex read the same rules.

## What's in here

- **Agent Table protocol** ([strategies/Agent_Table_Collaboration_Rules.md](strategies/Agent_Table_Collaboration_Rules.md)):
  lets separate agent sessions (planner, reviewer, coder, QA) hand off work
  through a shared `TABLE.md` and linked artifacts, without you copying
  messages between chats.
- **Agent Table skill** ([claude_skills/agent-table](claude_skills/agent-table), [codex_skills/agent-table](codex_skills/agent-table)):
  the transport for that protocol. Create, join, advance, pause, and resume a
  table. The `TABLE.md` format is identical for both tools, so Codex and
  Claude Code sessions can share a table, but handoff notifications do not
  cross harnesses: when the turn passes between them, you tell the receiving
  session to check the table.
- **Adversarial plan review** ([strategies/Agent_AdversarialPlanReviewer.md](strategies/Agent_AdversarialPlanReviewer.md),
  [codex_skills/adversarial-plan-review](codex_skills/adversarial-plan-review)):
  an independent challenge between plan approval and implementation. A
  separate session reconstructs the problem blind, then tests the approved
  plan for necessity, user impact, downstream effects, and technical design.
- **Optional planning seats** ([strategies/Agent_CoPlanner.md](strategies/Agent_CoPlanner.md),
  [strategies/Agent_EvidenceExperimentLead.md](strategies/Agent_EvidenceExperimentLead.md)):
  a co-planner for strategy and alternatives, and an evidence lead for
  research methods, bounded canaries and outcome measurement. Neither adds an
  approval gate.
- **PR review** ([agents/pr-review-specialist.md](agents/pr-review-specialist.md) for
  Claude Code, [codex_skills/pr-review](codex_skills/pr-review) for Codex):
  line-by-line GitHub PR review, submitted as one review with inline comments
  and a verdict. Read-only by design: neither can edit, push, or merge.
- **Implementation planning** ([guides/implementation-planning-guide.md](guides/implementation-planning-guide.md),
  [guides/implementation-plan-template.md](guides/implementation-plan-template.md)):
  what a strong plan contains and what reviewers most often block on,
  derived from independently approved plans and their first-round reviews.
- **Plan viewer** ([scripts/serve_implementation_plans.py](scripts/serve_implementation_plans.py)):
  renders a repo's `implementation_plans/` into a styled, linkable reading
  view at `http://127.0.0.1:8765/plans`. No build step.
- **Two work modes** ([strategies/Workflow_Feature_Discovery.md](strategies/Workflow_Feature_Discovery.md),
  [strategies/Workflow_Story_Delivery.md](strategies/Workflow_Story_Delivery.md)):
  `/feature-discovery` investigates a feature and produces a proposal, a
  feature plan, and paste-ready user stories; `/story-delivery` takes one
  story through plan, implementation, review, and pull request.
- **Engineering rules**: `AGENTS.md` holds authority, planning and safety
  rules plus a routing table; `strategies/Workspace_Operations.md` holds the
  detail it routes to (worktree hygiene, data access, feature flag wiring,
  test double fidelity, source-of-truth fixes and similar rules drawn from
  real defects). `scripts/check-workflow-instructions.py` keeps `AGENTS.md`
  inside Codex's instruction size limit.

## Requirements

Tested with Claude Code 2.1.283 and codex-cli 0.157.1 on Linux/WSL.

- `bash`, `git`, and `python3` (standard library only).
- The Claude Code `agent-table` skill needs the `ListAgents` and `SendMessage` tools
  (cross-session messaging). The Codex version needs the `codex queue` command.
- PR review needs `gh` authenticated to your GitHub host. For GitHub
  Enterprise: `gh auth login --hostname <your-ghe-host>`. The Claude reviewer
  also uses a GitHub MCP server when one is configured, and falls back to
  `gh` otherwise.
- On Windows, run Claude Code, Codex, and this toolkit inside WSL2. The
  agent-table helpers use Unix file locking (`fcntl`) and `os.getuid()`, so
  they do not run on native Windows Python, including from Git Bash.

## Set up a work machine

```bash
git clone <this repository's URL> ~/agentic-workflow
cd ~/agentic-workflow
scripts/install-local.sh --dry-run   # review what will change
scripts/install-local.sh             # install
```

The installer:

- copies the `/agent-table`, `/feature-discovery`, `/story-delivery`,
  `/adversarial-plan-review`, and `/review` commands and
  the `pr-review-specialist` agent into `~/.claude/`, and the skills into
  `~/.codex/skills/` (real copies, never symlinks: Codex silently ignores a
  skill whose `SKILL.md` is a symlink)
- adds a managed block to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` so
  the rules in `AGENTS.md` load in every repository; anything else in those
  files is kept
- backs up any file it would change as `<file>.bak-<timestamp>`, and is safe
  to re-run

Re-run it after pulling changes or moving the checkout. Restart open Claude
Code and Codex sessions afterward, since commands and skills load at session
start.

A repository's own `CLAUDE.md`/`AGENTS.md` and your team's written policies
take precedence over this toolkit wherever they conflict.

## Lower token cost on usage-based billing

Long agent sessions are cheap on a subscription and expensive on API or
enterprise usage credits. Two things drive the cost: every request rereads the
whole conversation, and on API billing the prompt cache expires after 5
minutes, so a seat that waits for a handoff rewrites its full context when it
wakes. Claude Code's default compaction point on 1M-context models is about
967k tokens, so a long-lived seat can carry several hundred thousand tokens
into every request.

Opt in with the installer:

```bash
scripts/install-local.sh --cost-settings
# If your account only has some models, point the opus/sonnet/haiku aliases at them:
scripts/install-local.sh --cost-settings --pin-models claude-opus-5,claude-sonnet-5,claude-sonnet-5
```

This merges [config/claude-cost-settings.json](config/claude-cost-settings.json)
into `~/.claude/settings.json`, keeping your other settings and backing up the
file first:

| Setting | Value | Why |
|---|---|---|
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | `200000` | Compact at 200k tokens instead of about 967k |
| `CLAUDE_CODE_PROMPT_CACHE_TTL` | `1h` | A main session that waits 5 to 60 minutes keeps its cache |
| `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` | `5m` | Subagents are short-lived; the 5 minute cache costs less to write |

Without `--pin-models`, the aliases resolve to the newest models, which a
restricted account may not have; Claude Code also uses the `haiku` alias for
background work.

What was measured: real Agent Table workstreams (plan, Opus plan review,
adversarial challenge, implementation, Opus code review), three tasks chained
per session, three runs per setup. The baseline was today's long-lived seat on
the 5 minute cache with no cap. The same work with the 200k cap, the 1 hour
main cache, the 5 minute subagent cache and Sonnet as the default subagent
model cost about a third less per workstream at equal quality. That run had no
cap-only arm; replaying its transcripts attributes most of the saving to the
cap. The Sonnet subagent default is not in this profile because the named Opus
reviewers did not use it. Savings grow with session length, because an
uncapped session's context keeps growing. Running each table turn as a fresh
short-lived session instead of a long-lived seat cut cost by about three
quarters in the same test; that dispatcher is not in this toolkit yet.

Things to know about these settings:

- They live in `env`, which takes precedence over `/autocompact` and the
  `autoCompactWindow` and `promptCacheTtl` settings. To change one, edit
  `env` in `~/.claude/settings.json`.
- 1 hour cache writes bill at twice the base input price (5 minute writes at
  1.25 times); they pay off when a session waits between 5 and 60 minutes.
- The subagent value (`5m`) is already the default. It also covers
  compaction, forks and other helper requests, and it overrides a subagent's
  own cache setting.
- The cache variables need Claude Code v2.1.242 or later.

Check that your account honors the 1 hour cache:

```bash
claude -p "hi" --output-format json
```

`usage.cache_creation.ephemeral_1h_input_tokens` above 0 means it does. If
only the 5 minute field has tokens, the compaction cap still provides most of
the saving. Restart open sessions after installing.

## Prepare each work repo

Agent Tables, plans, and runbooks live inside the work repo, at
`agent_tables/`, `implementation_plans/`, and `runbooks/`. Never put them in
this toolkit repo, which is public. Run this once per clone:

```bash
~/agentic-workflow/scripts/init-work-repo.sh /path/to/work-repo
```

It creates all three directories and lists them in that clone's
`.git/info/exclude`, which is local and never committed, so they will not
appear in `git status` or reach a team PR. Remove those lines if your team
decides to commit them.

To read plans in the viewer, from the work repo's root:

```bash
python3 ~/agentic-workflow/scripts/serve_implementation_plans.py
```

## Smoke test after installing

1. **Global rules.** In a new Claude Code session in any repo, ask "What does
   your AGENTS.md say about em dashes?" Then ask a new Codex session the same.
2. **Agent Table across sessions.** Open two Claude Code sessions in the same work
   repo. In the first, run `/agent-table create a table named smoke-test and join as
   reviewer; the implementer is <second session name>` (use `ListAgents` to
   get the name). Confirm the second session receives the handoff and can
   join. Delete `agent_tables/smoke-test` afterward.
3. **PR review.** On a PR you are allowed to comment on, ask the
   `pr-review-specialist` agent to review it. GitHub will not let you approve
   or request changes on your own PR, so on your own PR expect a `COMMENT`
   review that states the intended verdict.

## Maintaining this repo

This repo is a seed: edit here, re-run the installer, and let it diverge per
machine as needed. The agent-table helpers have automated tests:

```bash
python3 -m unittest discover -s claude_skills/agent-table/tests -p 'test_*.py'
python3 -m unittest discover -s codex_skills/agent-table/tests -p 'test_*.py'
python3 -m unittest discover -s scripts/tests -p 'test_merge_claude_settings.py'
```
