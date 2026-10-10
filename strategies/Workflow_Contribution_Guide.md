# Contributing to the agent workflow

Read this before changing `AGENTS.md`/`CLAUDE.md`, the table or role
contracts, the workflow skills, the installer, or their checks. General
scope, necessity, review and canary discipline lives in
[AGENTS.md](../AGENTS.md); use it without copying those rules into another
workflow document.

## Put each rule in its maintained home

| Concern | Maintained source |
|---|---|
| Universal authority and safety; task-reading routes | Root `AGENTS.md`; `CLAUDE.md` imports it |
| Detailed workspace rules the routes point to | [Workspace_Operations.md](Workspace_Operations.md) |
| Table state, ownership, handoff and independent review | [Shared table contract](Agent_Table_Collaboration_Rules.md) |
| Role and workflow judgment | The applicable `Agent_*.md` or `Workflow_*.md` in this directory |
| Harness commands and transport | `codex_skills/agent-table` and `claude_skills/agent-table` |
| Installation | `scripts/install-local.sh` |

Change the canonical source, update its consumers, and remove contradictory
operative wording in the same change. Historical reviews remain evidence, not
instructions to copy. A pointer should say when to read its destination.

## Check the affected instruction path

Run the mechanical checks for any change to `AGENTS.md`, `CLAUDE.md`,
`Workspace_Operations.md` or this guide:

```bash
python3 -m unittest discover -s scripts/tests -p test_workflow_instructions.py
python3 scripts/check-workflow-instructions.py
```

The `workflow-instructions` CI job runs the same checks: the root size
budget, the `CLAUDE.md` pairing, and repository-owned Markdown links and
anchors in those three documents. It does not establish that a rule kept its
meaning, and it does not prove a running session adopted new text.

Keep `AGENTS.md` within its budget. Codex reads a project `AGENTS.md` only up
to its `project_doc_max_bytes` limit (32 KiB by default) and silently drops
the rest, so put detail in `Workspace_Operations.md` or a role contract and
route to it. Test Codex loading with the default limit, for example
`codex debug prompt-input` from the toolkit checkout with a fresh
`CODEX_HOME`, so a local override cannot hide truncation.

## Keep source, installed copies and sessions together

The toolkit is the source; `scripts/install-local.sh` copies it into
`~/.claude` and `~/.codex`. Installed Codex `SKILL.md` files must be real
files, never symlinks: Codex skill discovery silently omits a skill whose
`SKILL.md` is a symlink. Re-run the installer after a change, then restart
the session; installed files do not update a running session's context.

For harness-independent workflows, the Claude command is a thin pointer to
the canonical Codex `SKILL.md` and requires reading the whole contract. Do not
paraphrase guardrails into separate copies. The `agent-table` skill is the
exception because its harness mechanics differ; it keeps a real adapter per
harness. Update all applicable sources and pointers together.

For changed helpers, run both harnesses' `agent-table` test suites and a
disposable-table canary before relying on the change. Inspect the claim,
handoff and resulting artifact, not only a successful command.

## Close the existing work record

Record the exact source identity, verified outcome, remaining adoption work
and next actor in the existing table or tracker ticket. This guide creates no
additional approval seat. Source merge, installation and active-session
adoption are distinct results.
