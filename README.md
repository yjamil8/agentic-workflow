# agentic-workflow

A portable, company-agnostic multi-agent engineering toolkit for Claude Code
and Codex, extracted and genericized from a larger production project's
internal agent tooling. No product code, no company-specific policy; the
examples in these docs (service names, ports, stacks) are illustrative and
meant to be adapted.

Start with [AGENTS.md](AGENTS.md) — it explains the repo layout and pulls
everything else together. `CLAUDE.md` is a symlink to it, since both Claude
Code and Codex read the same file by different conventional names.

## What's in here

- **Agent Table protocol** ([strategies/Agent_Table_Collaboration_Rules.md](strategies/Agent_Table_Collaboration_Rules.md)) —
  a file-based collaboration protocol so separate agent sessions (planner,
  reviewer, coder, QA, ...) can hand off work without the owner copy-pasting
  between chats. `TABLE.md` is the shared state; artifacts are linked, not
  pasted.
- **Rally** ([claude_skills/rally](claude_skills/rally), [codex_skills/rally](codex_skills/rally)) —
  the transport for the protocol above: create/join/advance/pause/resume a
  table, one implementation per harness, byte-identical `TABLE.md` format so
  a Codex session and a Claude Code session can hold seats at the same table.
- **Adversarial plan review** ([strategies/Agent_AdversarialPlanReviewer.md](strategies/Agent_AdversarialPlanReviewer.md),
  [codex_skills/adversarial-plan-review](codex_skills/adversarial-plan-review)) —
  a required independent challenge gate between ordinary plan approval and
  implementation: a separate session reconstructs the problem blind, then
  tests the approved plan against necessity, customer sense, second/third
  order effects, and technical design before implementation can start.
- **PR review** ([agents/pr-review-specialist.md](agents/pr-review-specialist.md) for
  Claude Code, [codex_skills/pr-review](codex_skills/pr-review) for Codex) —
  thorough line-by-line GitHub PR review with a stable severity taxonomy,
  posting inline comments and a final verdict.
- **AGENTS.md discipline sections** — scope/planning discipline, feature-flag
  wiring discipline, test-double fidelity, source-of-truth fix discipline,
  and a few other rules distilled from real defects caught in production use,
  generalized away from any one product.

## Installing locally

This repo is a one-time seed, not a continuously synced mirror: copy it into
your live Claude Code / Codex config once, then let it diverge on the work
machine as needed.

```bash
scripts/install-local.sh --dry-run   # see what would be installed
scripts/install-local.sh             # actually install
```

This copies (never symlinks — see the script's header comment for why)
commands and agents into `~/.claude/...` and skills into `~/.codex/skills/...`.
Restart any open session afterward; command/skill lists are read at session
start.

## Using it in a project

Drop `AGENTS.md` (and the `CLAUDE.md` symlink) into a repo, or point that
repo's own `AGENTS.md` at this one. Create `agent_tables/` and
`implementation_plans/` directories (already present here as empty
placeholders) wherever your actual work lives, and adjust the illustrative
paths/examples in `strategies/Agent_Table_Collaboration_Rules.md` and
`AGENTS.md` to match your stack.
