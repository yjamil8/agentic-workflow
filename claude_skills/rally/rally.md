# Rally (Claude Code)

One goal, named roles, durable handoffs. Coordinate existing Claude Code
sessions; do not spawn new agents, a daemon, a watcher, a new approval
process, or a second source of truth.

This is a fork of the Codex `$rally` skill
([../../codex_skills/rally/SKILL.md](../../codex_skills/rally/SKILL.md)), not
an edit of it. Nothing here changes that skill or its script. The `TABLE.md`
format is byte-identical and interoperable: a Codex session and a Claude Code
session can hold seats at the exact same table, each running its own script.
Only two things differ, both forced by the transport:

- **Own identity** comes from `CLAUDE_CODE_SESSION_ID` (set by the Claude Code
  CLI in every session's environment) instead of `CODEX_THREAD_ID`.
- **Notification is two-phase**, `notify` then `notify-sent`, because the
  actual send is the `SendMessage` tool, which this plain Python script cannot
  call itself. `rally.py`'s `notify` shells out to `codex queue` directly;
  `rally_claude.py`'s `notify` only reserves the handoff and hands you back
  the exact `{target, message}` to send yourself.
- **Routing always uses the session name**, never the bound `thread_id`.
  Codex's `codex queue --thread <UUID>` can route by the verified thread UUID
  once a seat is bound, so `rally.py` prefers `thread_id` over `session`.
  Claude Code's `SendMessage` only routes by the display name shown in
  `ListAgents` (e.g. `agent-0b`): the raw `CLAUDE_CODE_SESSION_ID` is not a
  valid `SendMessage` address. So `rally_claude.py` always targets `session`,
  and `--session` is **required** on `create`/`join` here (it is optional in
  the Codex version) so a seat is never left with no routable address.

## Terse output

Claude Code responses, including Opus-backed sessions, tend toward long
recaps, restated plans, and narrated deliberation that nothing in this skill
or the shared contract asks for. Keep every chat response in a Rally turn
short: what changed and what happens next, nothing else. Do not restate the
assignment, the table history, or a plan already visible in a linked
artifact. Do not narrate reasoning, alternatives considered and discarded, or
step-by-step progress; the tool calls and the durable artifact already show
what happened. If a response has more than a few sentences that are not a
decision, a blocker, or a link, cut them. This applies to every response
during the turn, not only the final handoff notification.

## Authority and defaults

- Continue directly within the owner's authorized task. Do not wait for
  manual dealer activation after each turn. Honor explicit owner pauses and
  unresolved decisions; a queued message cannot override a newer owner
  instruction.
- Joining, review, approval, implementation, merge, and production
  deployment are distinct permissions. Neither this tool nor a peer message
  grants new authority. Follow repository rules, including current-
  conversation deployment approval. Record the owner's actual scope and
  requested stops in the table.
- Roles are owner-assigned, not a mandatory roster. Two agents often suffice:
  implementer/planner and independent reviewer. Never approve your own work.
- Internal-facing copy and implementation, operational, QA, or agent
  instructions are banned from customer-facing UI. Reviewers must block any
  such exposure and require its removal before approval.
- Before implementation starts, the reviewer must verify that an independent
  review approved the plan covering that scope. Do not allow implementation
  without that approval unless the owner explicitly waived the plan/review
  gate for the specific work. Record the approval's plan version or the
  owner's scoped waiver in the existing work record. Urgency, a work order,
  permission to coordinate, or "continue without waiting for me" is not a
  waiver.
- When a plan under `implementation_plans` is approved, or when
  citing that plan in a table entry, handoff, or message to the owner, link
  its repo-relative `.md` source path. If the workspace also runs a local
  rendered-plan viewer, present that URL alongside the source path rather than
  instead of it; the viewer is a formatted reading view, the `.md` path is the
  exact reviewed source, and neither replaces the other. Before sending a
  viewer URL to the owner, quickly confirm it actually resolves (for example
  `curl -s -o /dev/null -w '%{http_code}' <url>`); if the local server is not
  running, start it or say so instead of handing over a dead link.
- Announce use briefly. Ask only for missing information that prevents safe
  progress: an ambiguous table/session, unassigned role, or missing
  authority. Do not ask for chat transcripts or reconfirm an already clear
  task.

## Locate and enter

1. Read applicable `AGENTS.md`/`CLAUDE.md`, then read
   [`strategies/Agent_Table_Collaboration_Rules.md`](../../strategies/Agent_Table_Collaboration_Rules.md)
   in full. Do this before creating a table as well as before joining one; it
   is the actual contract for every seat's duties (the UI presentation
   approval gate, screenshot requirements, Approval Receipts, review-finding
   handling), not a legacy-tables-only reference. This document is the
   transport/routing layer only, exactly as described above. Use an explicit
   table path when supplied; otherwise use `rg --files --hidden -g TABLE.md`
   in the workspace's table directory (`agent_tables` at this repo's root).
   Match the exact table name or uniquely matching goal. If more than one
   matches, ask which one. Never silently create another table when the
   request is to join.
2. On **create and join**, first check for an existing matching table.
   Create only on explicit owner instruction. Use a shared absolute path,
   normally `agent_tables/<goal-slug>/TABLE.md` (or `agent_tables`
   elsewhere). Record the goal, authorized scope, role assignments, and
   first useful task. Read-only coordination does not need an implementation
   plan; implementation follows the plan gate above. Do not add unrelated
   gates.
   The creating agent must give the owner the exact `table_id` UUID and a
   clickable link to the canonical absolute `TABLE.md` path immediately
   after successful creation, and include both in its final response so the
   owner can pass them to other agents. Read the ID from the helper output
   or table; do not substitute the table name or a session name. Report
   these even if peer notification fails; do not wait for the owner to ask.
   After creation, claim the first turn with `join` if it is yours;
   otherwise notify the assigned first role and remain registered in
   standby.
3. Use the helper below for new tables. Call `ListAgents` first: its header
   line ("This session is `<name>` `[<ref>]`...") gives you the exact
   `--session` value to pass for yourself; its rows give you the exact
   `--session` value for a counterpart. Your own verified identity comes
   from `CLAUDE_CODE_SESSION_ID`; if unavailable, use a verified UUID with
   `--thread`. Never guess from log timestamps or "the most recently active
   session." The owner supplies a counterpart's exact session name (append
   its `[ref]` only when `ListAgents` or a `SendMessage` error shows one is
   needed for disambiguation). Do not rename, replace, or spawn that chat.
4. Joining binds the invited name to the joining session's verified
   `CLAUDE_CODE_SESSION_ID`. Subsequent turn-claim checks use that ID; all
   routing still uses the session name. A session name is an address, not
   proof of product authority. Resolve ambiguous names instead of selecting
   a best match. Each session must be able to read the same canonical table
   and relevant worktrees.
5. Read current table state and the linked inputs needed for your
   assignment, not every historical artifact. Inspect source/evidence
   appropriate to your role. If another role owns the turn, register and
   yield; do not take its work or ask the owner to activate you. Do not
   poll.

## Helper: new tables

Run `python3 <skill-dir>/scripts/rally_claude.py --help`. Python 3 and the
native `ListAgents`/`SendMessage` tools are required; no external CLI is
called. Resolve `<skill-dir>` to the directory containing this doc
(`claude_skills/rally`). All examples use placeholder values; use
the real owner-provided scope and session names.

```bash
# Called by the reviewer; the existing implementer receives the first task.
python3 <skill-dir>/scripts/rally_claude.py create --table /shared/agent_tables/example/TABLE.md \
  --name example --goal 'The owner goal' --scope 'Authorized work and explicit stops' \
  --role reviewer --session reviewer-session-name --peer implementer=implementer-session-name \
  --first-role implementer --assignment 'Inspect the affected code and propose the smallest sufficient plan.'

# Phase 1: reserve the handoff. Never sends anything by itself.
python3 <skill-dir>/scripts/rally_claude.py notify --table /shared/agent_tables/example/TABLE.md
# -> {"result": "ready_to_send", "target": "implementer-session-name", "message": "...",
#     "attempt_id": "...", "table_id": "UUID", "turn": 1}

# Now call the SendMessage tool yourself:
#   {"to": "implementer-session-name", "message": "<the printed message>"}

# Phase 2: record what SendMessage actually did. Do this immediately after, always.
python3 <skill-dir>/scripts/rally_claude.py notify-sent --table /shared/agent_tables/example/TABLE.md \
  --table-id UUID --turn 1 --attempt-id ATTEMPT_ID --status queued
# If SendMessage clearly failed instead: --status uncertain --error 'what happened'

# Recipient: take the table ID and turn from the SendMessage text, not an old chat.
python3 <skill-dir>/scripts/rally_claude.py join --table /shared/agent_tables/example/TABLE.md \
  --role implementer --session implementer-session-name --table-id UUID --turn 1

# Write the real artifact first. Then hand off and ring the doorbell once.
python3 <skill-dir>/scripts/rally_claude.py advance --table /shared/agent_tables/example/TABLE.md \
  --table-id UUID --role implementer --turn 1 --to reviewer \
  --assignment 'Review the linked candidate.' --summary 'Ready for independent review.' \
  --artifact /shared/path/to/candidate.md
python3 <skill-dir>/scripts/rally_claude.py notify --table /shared/agent_tables/example/TABLE.md
# -> ready_to_send with a new target/message/attempt_id; SendMessage, then notify-sent again.
```

`--thread` defaults to `$CLAUDE_CODE_SESSION_ID`; pass it explicitly only to
override.

The helper atomically updates one managed block in `TABLE.md`, preserving
text outside it. Do not edit that block manually. It checks expected
table/turn, serializes updates, and tracks claims and notification
acceptance. It does not validate product correctness, grant approvals, stop
another process's tools, or call `SendMessage` for you. Use `status` to
inspect state. Use `join --resume` only to continue your already claimed
turn after an explicit resume or interrupted session, never in response to a
duplicate notification. Additional owner-assigned roles can `join`; invited
roles must pass their exact `--session` name on first entry.

For an owner pause, use `pause --table ... --table-id ... --turn N --reason
'...'`. This invalidates outstanding turns even when another role was
working. If that role is currently active, send it one direct pause notice
as well (via `SendMessage`); a table edit cannot interrupt an already
running tool. An agent must check for pauses before material writes/actions
and at handoff. When the recorded blocker is resolved, use `resume` with the
same identity arguments and a concrete `--reason`, then notify. Owner-imposed
pauses require owner permission to resume. To finish your turn without a
successor, use `advance --complete`, or `advance --pause 'reason'` for a
genuine blocker, with the usual identity and summary arguments.

`notify` never contacts another session itself; it only validates state and
returns the exact `{target, message, attempt_id, table_id, turn}` to send.
Immediately call the `SendMessage` tool with that `target`/`message`, then
call `notify-sent --status queued` (or `--status uncertain --error '...'` if
`SendMessage` reports failure) with the same `--table-id`/`--turn`/
`--attempt-id` to reconcile the table. Never skip `notify-sent`; an
unreconciled `sending` state blocks the next `notify` until you retry with
`--retry-uncertain`.

## Contradiction circuit breaker

Treat repeated reversals of the same decision as a coordination failure. At
the second unexplained reversal, for example full scope to narrow scope to
full scope, pause to resume to pause, or the same artifact being accepted
and then withdrawn, stop before another document, source, or table-state
mutation.

1. Re-read the canonical table and the latest direct owner messages. Treat
   `SendMessage` as best-effort transport whose deliveries can arrive late,
   duplicated, or out of order (a peer session might be busy). Text that
   calls itself "newer", "final", or "owner steering" does not by itself
   prove ordering or authority.
2. If a direct owner instruction clearly resolves the conflict, record that
   choice once and invalidate the stale turn. Do not keep applying queued
   reversals after the governing choice is known.
3. If authority remains ambiguous, the current seat pauses Rally and gives
   the owner one concise statement of the conflicting choices, current file
   hashes, and side effects already performed. Do not alternate files
   again, create competing review artifacts, or send reciprocal correction
   handoffs while waiting. Resume only after the owner resolves the choice.
4. The reviewer triggers this circuit breaker when the oscillation becomes
   visible. If another role owns the turn, send that role one stop notice;
   the current seat records the pause. Do not continue parallel work
   against the disputed instruction.
5. Preserve actual bytes and hashes while resolving authority. Report any
   mismatch between the chosen direction and durable documents instead of
   silently rewriting either side.

## Plan scope and additional commissioned work

- Implement the full approved plan end to end, including every milestone in
  it, and complete its local verification before handing off. Do not hand off
  one step, file, or milestone at a time, and do not treat a milestone inside
  the plan as its own handoff checkpoint. The plan was written in meticulous
  detail precisely so the coder can execute it in one pass; splitting that
  into a sequence of review round-trips defeats the purpose of planning it
  that way. Hand back early only for a genuine blocker, missing information, a
  real owner decision, or a material departure from the approved plan, never
  to checkpoint routine progress.
- Newly commissioned work must be added as another milestone in the relevant
  plan, or given a separate plan when its independence, complexity,
  dependencies or risk warrant that separation. Inspect affected
  source/contracts first and explain the choice briefly; neither a message
  nor a work-order brief is an approved implementation plan.
- Obtain independent review approval of the added milestone or separate
  plan before implementing that new scope, unless the owner explicitly
  waives the gate for it. Preserve the owner's sequence, including "after
  current work." Unaffected approved work may continue. Fixing a
  demonstrated defect within approved scope is not automatically a new
  commissioned milestone.
- Review the changed scope without restarting unchanged plan approvals.
  Keep related changes in a coherent candidate and consolidate handoffs,
  final builds and evidence where practical. A milestone does not by itself
  require another worktree, PR, screenshot packet or review ceremony for
  every small edit. Split for a concrete dependency, risk or owner
  instruction, not habit.

## Complete handoffs

- Assume the receiving session has none of the owner's private conversation
  context. The agent asked to coordinate owns the due diligence: re-read
  the relevant owner instructions and inspect the source/artifacts needed
  to make the assignment accurate before handing off.
- Put enough context in the existing durable assignment or a linked brief
  for the recipient to act without guessing: the actual problem and desired
  outcome; agreed behavior/copy and examples or screenshots; scope/
  exclusions; constraints and owner decisions; inspected source/worktree
  refs and known gaps; acceptance criteria; current work/ordering; and who
  acts next, what they must deliver, and which approval is required.
  Distinguish verified findings, proposals and unknowns. Scale detail to
  the task, not a mandatory packet size.
- Check that linked artifacts exist, identify the intended versions, and
  are accessible in the shared workspace. Resolve material ambiguity from
  available evidence or ask the owner the specific missing question; do
  not export an unresolved choice as a supposed requirement or expect the
  owner to relay it.
- Send a short notification pointing to that complete assignment, not an
  ambiguous "do what we discussed" message or a dense table-only
  substitute. The recipient checks scope and approval before
  implementation and requests missing context directly from the sender.
- Before completing a turn that ran Angular work, apply the root `AGENTS.md`
  cache thresholds. Clean the cache or record its exact path, size, reason for
  deferral, and next cleanup actor; unexplained agent-created caches or
  worktrees make the handoff incomplete.

## Handoff ownership and stopping rules

- Every handoff names the next actor and action in the existing
  assignment: "Reviewer: assess this evidence now" or "Status only;
  implementer continues." A status update does not transfer the turn. If a
  peer stops expecting a decision, resolve that mismatch directly instead
  of leaving both sessions waiting.
- Unresolved findings may be submitted for assessment. Include the exact
  source, available evidence, remaining uncertainty and requested
  decision; do not wait for every finding to be green before handing off.
- Do not block substantive review on a packet name, H-series label or
  extra document when exact commits/plan bytes and accessible evidence
  suffice. Preserve table identity, turn ownership, authority and replay
  checks; resolve missing safety-critical information, not cosmetic
  packaging.
- End bounded investigation with a disposition: demonstrated fix,
  evidenced harness issue, documented residual risk for explicit
  acceptance by the authorized decision-maker, or a precise blocker and
  next actor. Later passes do not prove an earlier failure fixed. Do not
  demand indefinite retesting or an unknowable historical cause after
  useful evidence is exhausted.
- Send decisions and requests directly to the responsible peer after
  recording them. A reply visible only in the owner's chat does not notify
  that peer. Use the existing single-notification/replay rules, not
  acknowledgement loops.
- Before yielding, make the next actor and concrete action explicit in
  durable state. A pending handoff is a valid waiting state; a queued
  `SendMessage` is not receipt, review or completion. If neither agent can
  proceed, surface the exact missing owner decision or external
  prerequisite instead of silently stopping.
- **No orphaned next step.** See "No Orphaned Next Step" in
  `Agent_Table_Collaboration_Rules.md`: never end a turn on a stated
  intention to implement, review, or coordinate unless that work was
  actually done or explicitly paused with a reason. A turn that ends on
  "implementing now" with no artifact, diff, or pause reason behind it has
  not advanced the table.

## Handoff and replay discipline

- Write the result first, update the table second, notify last. Reviews
  name exact plan bytes or application commits and useful affected
  evidence. One compact review/handoff is enough; do not review a
  bookkeeping-only approval commit or introduce finalizer ceremonies.
- Messages are doorbells: table path, table ID, turn, role. The table and
  linked artifacts are authoritative. Verify all three identifiers before
  taking work. A stale turn, different table ID, already claimed turn,
  pause, or completed table means **no repeated work, approval, or reply
  notification**.
- `notify`/`notify-sent` records your outbound `SendMessage` attempt, not
  the recipient's receipt. Do not resend accepted messages because the
  recipient has not replied. A join records receipt; no ACK-of-ACK or
  test-probe loop is needed.
- If delivery is uncertain, inspect table state first. `notify
  --retry-uncertain` is a single explicit retry only after investigating
  why the prior attempt was marked uncertain; it is not a polling strategy.
  If `SendMessage`/`ListAgents` is unavailable (for example, cross-session
  messaging is disconnected), preserve the pending handoff and report the
  actual transport blocker without inventing a new router.
- If a review/fix loop makes no substantive progress, surface the
  unresolved decision to the owner; do not invent additional scope to keep
  agents busy.
- Keep the owner updated on outcomes and material scope increases. Direct
  continuation does not mean silent work or unlimited task expansion.

## A restarted session loses its claim

`CLAUDE_CODE_SESSION_ID` changes when a session is restarted. The seat comes back
under the same `ListAgents` name and is addressable as before, but the table
binds claims to the session id, not the name. Two consequences:

- `registered()` no longer matches it, so it cannot `notify` until it re-joins.
- `join` on the turn it was holding fails, because that turn is claimed by the
  previous session id. `join --resume` does not help: it continues *your own*
  claimed turn, and this is a different identity.

Recovery, run by the seat that is **not** holding the turn:

```bash
python3 <skill-dir>/scripts/rally_claude.py pause --table ... --table-id ... --turn N   --reason 'Seat restarted; clearing the stale claim from the prior session id.'
python3 <skill-dir>/scripts/rally_claude.py resume --table ... --table-id ... --turn N+1   --reason '...'
```

`pause` and `resume` each advance the turn, so the reissued turn is `N+2`. Read
it from the command output rather than assuming; then `notify` and tell the
returning seat the new turn number explicitly, because it will otherwise try the
old one. The returning seat `join`s the new turn, which rebinds its name to the
new session id and re-registers it.

There is no `reclaim` command and none is wanted: `pause` plus `resume` already
does this with existing machinery. Use the `--reason` string to record that it
was a restart rather than an owner pause, so the table's history stays truthful.

When a restart is planned rather than forced, do it before a turn is claimed.
Restarting mid-turn always costs a reissue.

## Follow-up after a table is complete

A completed table cannot be reopened, and should not be: `resume` expects a
recorded pause, `join` will not claim a completed turn, and `advance` expects a
claim. Do not manufacture a pause to force it open, and do not create a second
table for the same goal.

Send the assignment with `SendMessage` directly to the responsible seat, and:

- carry enough context for the recipient to act without the table, because there
  is no live assignment field to read
- say explicitly that the message is the assignment and that the table is
  complete and was deliberately not reopened
- keep the original table, plan and artifacts authoritative, and write new
  evidence into the same artifact directory
- there is no `notify`/`notify-sent` pair to reconcile here, because no turn was
  reserved; the message is the whole handoff

If the follow-up needs its own plan, review gate and several turns, it is a new
workstream and gets a new table with a distinct goal. The test is whether it
shares the completed goal or replaces it, not whether it touches the same files.

## Existing non-Rally tables

Keep their canonical file, turn, artifacts, and history. Do not run
`create` over them or introduce a parallel Rally state file. Follow their
current format; the role-specific rules are the same Agent_Table_Collaboration_Rules.md
already required at entry above, not a separate contract for this case.
Update only the current assignment/state and
session mappings needed for the authorized handoff. Re-read before writing;
only the current seat writes workflow state. Register an idle seat through
the current writer if a manual edit could race. Record the accepted turn so
duplicates cannot restart it.

Notify once with `SendMessage`, addressed to the exact session name; include
the exact table path, turn, and role. Check current state before acting.
Retain explicit owner stops; do not inherit obsolete manual dealer
activation when the owner has authorized direct continuation. A conflicting
unresolved contract needs a narrow correction, not a silent workflow
migration.

## Interoperating with the Codex `$rally` table

The `TABLE.md` JSON schema has nothing Codex-specific in it: `thread_id` and
`session` are opaque strings either tool can read and write. A workstream
can legitimately mix seats: a Codex session as planner, a Claude Code session
as independent reviewer, on the exact same table. When you join a table
created by `$rally`, everything in this doc still applies; you simply run
`rally_claude.py` instead of `rally.py`, and any Codex participant already
seated keeps using its own script unchanged.
