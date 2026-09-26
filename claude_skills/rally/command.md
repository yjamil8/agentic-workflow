Rally: coordinate with other Claude Code sessions on one shared goal using the Agent Table protocol: $ARGUMENTS

Read `<agentic-workflow-root>/claude_skills/rally/rally.md` in full and follow it exactly for this request. Do not improvise a different protocol, and do not confuse it with the separate Codex `$rally` skill in `<agentic-workflow-root>/codex_skills/rally`: same table format, different script and transport.

If that file is not present in this workspace, tell the user it is missing and ask where the equivalent protocol doc lives instead of inventing one.

Quick orientation, in order:

1. Call `ListAgents` to learn your own session name/ref and see live peer sessions. This is also where you get the exact `--session` value for yourself and for any counterpart.
2. Decide whether this is "create and join" a new table or "join" an existing one. Use `rg --files --hidden -g TABLE.md` under `agent_tables/` at the root of the work repo you are in to check for an existing match first; never silently create a second table for the same goal.
3. Run `python3 <agentic-workflow-root>/claude_skills/rally/scripts/rally_claude.py --help` for the exact command surface (`create`/`join`/`advance`/`pause`/`resume`/`notify`/`notify-sent`/`status`).
4. `notify` only reserves a handoff; it never sends anything. Take its `target`/`message`, call the `SendMessage` tool yourself, then call `notify-sent` with `--status queued` (or `uncertain --error '...'` on failure). Never skip `notify-sent`.
5. Only the current seat may change table state. If another seat owns the turn, register and yield; do not take its work or ask the owner to activate you.
