#!/usr/bin/env python3
"""Small shared-file handoff helper for Claude Code sessions. No daemon; notifications are not authority.

Forked from ../../codex_skills/rally/scripts/rally.py. The TABLE.md format is
identical and interoperable with that Codex version; only two things differ:
own-identity comes from CLAUDE_CODE_SESSION_ID instead of CODEX_THREAD_ID, and
notification is a two-phase notify/notify-sent pair because the actual send is
the SendMessage tool call, which this plain script cannot make itself.
"""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid


BEGIN = "<!-- rally:begin -->"
END = "<!-- rally:end -->"


def own_thread(args):
    value = args.thread or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    try:
        return str(uuid.UUID(value))
    except ValueError:
        raise ValueError("Missing verified session UUID: CLAUDE_CODE_SESSION_ID or --thread")


def block(state):
    links = "\n".join(f"- [{Path(p).name}](<{p}>)" for p in state["artifacts"])
    return (f"{BEGIN}\n```json\n{json.dumps(state, indent=2)}\n```\n"
            f"\n### Active artifacts\n\n{links or 'None yet.'}\n{END}")


def read_table(path):
    content = path.read_text()
    if content.count(BEGIN) != 1 or content.count(END) != 1:
        raise ValueError("Not a Rally table; preserve the existing format and follow its contract")
    managed = content.split(BEGIN, 1)[1].split(END, 1)[0]
    state = json.loads(managed.split("```json\n", 1)[1].split("\n```", 1)[0])
    if state["rally"] != 1:
        raise ValueError("Unsupported Rally format")
    return content, state


def write_table(path, content, state):
    before, after = content.split(BEGIN, 1)[0], content.split(END, 1)[1]
    fd, temp = tempfile.mkstemp(prefix=".rally-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(before + block(state) + after)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@contextmanager
def locked(path):
    # Stable per-user lock inode, outside the repository; never unlink live locks.
    folder = Path(tempfile.gettempdir()) / f"rally-claude-locks-{os.getuid()}"
    folder.mkdir(mode=0o700, exist_ok=True)
    key = hashlib.sha256(str(path).encode()).hexdigest()
    with (folder / key).open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def check_turn(args, state):
    if args.table_id != state["table_id"] or args.turn != state["turn"]:
        raise ValueError("Stale table ID or turn; no action taken")


def registered(state, thread):
    if not any(p["thread_id"] == thread for p in state["participants"].values()):
        raise ValueError("Session is not registered at this table")


def advance_state(state, role, status, assignment=None):
    state.update(turn=state["turn"] + 1, current_role=role, state=status, claim=None)
    if assignment is not None:
        state["assignment"] = assignment
    state["notification"] = {"status": "pending" if status == "ready" else "none"}


def create(args, path):
    if path.exists():
        raise ValueError("Table already exists; join it, do not overwrite it")
    thread = own_thread(args)
    participants = {args.role: {"session": args.session or thread, "thread_id": thread}}
    for peer in args.peer:
        role, sep, session = peer.partition("=")
        if not sep or not role.strip() or not session.strip() or role in participants:
            raise ValueError("Each --peer must be a distinct role=exact-session-name")
        participants[role] = {"session": session, "thread_id": None}
    first = args.first_role or args.role
    if first not in participants:
        raise ValueError("First role must be a named participant")
    state = dict(rally=1, table_id=str(uuid.uuid4()), name=args.name,
                 goal=args.goal, scope=args.scope, workspace=str(Path.cwd()),
                 participants=participants, turn=1, current_role=first, state="ready",
                 assignment=args.assignment, claim=None, artifacts=[], last_result=None,
                 pause_reason=None, notification={"status": "pending"})
    path.parent.mkdir(parents=True, exist_ok=True)
    write_table(path, f"# {args.name} - Rally table\n\n"
                f"The managed block is authoritative; update it with Rally.\n\n{BEGIN}{END}\n", state)
    return state


def change(args, state, path):
    thread = own_thread(args)
    if args.command == "join":
        if (args.turn is None) != (args.table_id is None):
            raise ValueError("Supply both --turn and --table-id for a notification")
        if args.turn is not None:
            check_turn(args, state)
        seat = state["participants"].get(args.role)
        if seat and seat["thread_id"] not in (None, thread):
            raise ValueError("Role is bound to a different session; owner must resolve replacement")
        if seat and seat["thread_id"] is None and seat["session"] not in (args.session, thread):
            raise ValueError("Pass the exact invited --session name to bind your own UUID")
        state["participants"][args.role] = seat or {"session": args.session or thread, "thread_id": thread}
        state["participants"][args.role]["thread_id"] = thread
        if state["current_role"] != args.role:
            return "standby"
        if state["state"] in ("paused", "complete"):
            return state["state"]
        if state["claim"]:
            return "resumed" if args.resume else "already_claimed"
        state.update(state="working", claim=thread)
        state["notification"] = {"status": "received"}
        return "claimed"

    check_turn(args, state)
    registered(state, thread)
    if args.command == "pause":
        if state["state"] == "complete":
            raise ValueError("Completed table; do not reopen through pause")
        advance_state(state, state["current_role"], "paused")
        state["pause_reason"] = args.reason
        return "paused"
    if args.command == "resume":
        if state["state"] != "paused":
            raise ValueError("Only a paused table can be resumed")
        advance_state(state, state["current_role"], "ready")
        state["resume_reason"] = args.reason
        state["pause_reason"] = None
        return "ready"

    if (state["state"] != "working" or state["current_role"] != args.role
            or state["claim"] != thread):
        raise ValueError("Only the current claimed role may advance this turn")
    if args.to and (args.to not in state["participants"] or not args.assignment):
        raise ValueError("Handoff requires a registered/invited destination and --assignment")
    artifacts = []
    for value in args.artifact:
        artifact = Path(value)
        artifact = (artifact if artifact.is_absolute() else path.parent / artifact).resolve()
        if not artifact.is_file():
            raise ValueError(f"Write the artifact before handing off: {artifact}")
        artifacts.append(str(artifact))
    # Keep previous inputs when a bookkeeping/status handoff has no new artifact.
    if artifacts:
        state["artifacts"] = artifacts
    state["last_result"] = dict(role=args.role, turn=state["turn"], summary=args.summary,
                                artifacts=artifacts)
    status = "complete" if args.complete else "paused" if args.pause else "ready"
    advance_state(state, args.to or args.role, status, args.assignment)
    state["pause_reason"] = args.pause
    return status


def notify(args, path):
    """Phase 1: validate and reserve the pending handoff. Never sends anything.

    The caller must immediately call the SendMessage tool with the returned
    target/message, then call notify-sent to reconcile the reservation.
    """
    with locked(path):
        content, state = read_table(path)
        registered(state, own_thread(args))
        delivery = state["notification"]["status"]
        if state["state"] != "ready" or delivery in ("queued", "received", "none"):
            return {"result": "not_sent", "state": state["state"], "notification": delivery}
        if delivery in ("sending", "uncertain") and not args.retry_uncertain:
            return {"result": "uncertain; inspect before an explicit retry", "notification": delivery}
        seat = state["participants"][state["current_role"]]
        target = seat["session"]
        table_id, turn = state["table_id"], state["turn"]
        attempt_id = str(uuid.uuid4())
        state["notification"] = dict(status="sending", target=target, attempt_id=attempt_id)
        write_table(path, content, state)
        message = (f"Rally handoff: table {path}; table_id {table_id}; turn {turn}; "
                   f"role {state['current_role']}; invited session {seat['session']}. "
                   f"Use /rally ({Path(__file__).resolve().parents[1] / 'rally.md'}) "
                   "to read the current table and join with these identifiers. "
                   "Ignore stale/claimed/paused/completed work and honor newer owner instructions. "
                   "No ACK or probe reply required.")
        return {"result": "ready_to_send", "target": target, "message": message,
                "attempt_id": attempt_id, "table_id": table_id, "turn": turn}


def notify_sent(args, path):
    """Phase 2: record what the SendMessage call actually did. Call once, right after it."""
    with locked(path):
        content, state = read_table(path)
        registered(state, own_thread(args))
        current = state["notification"]
        stale = not (state["table_id"] == args.table_id and state["turn"] == args.turn
                     and current.get("attempt_id") == args.attempt_id)
        if stale:
            return {"result": "stale; table advanced before acknowledgement", "notification": current}
        outcome = {"status": args.status, "target": current.get("target"), "attempt_id": args.attempt_id}
        if args.error:
            outcome["error"] = args.error
        state["notification"] = outcome
        write_table(path, content, state)
        return {"result": "recorded", "notification": outcome}


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("create", "join", "advance", "pause", "resume", "notify", "notify-sent", "status"):
        sub = commands.add_parser(name)
        sub.add_argument("--table", required=True, help="Canonical shared TABLE.md path")
        sub.add_argument("--thread", help="Verified own session UUID; otherwise CLAUDE_CODE_SESSION_ID")
        if name in ("join", "advance", "pause", "resume", "notify-sent"):
            sub.add_argument("--table-id", required=name != "join")
            sub.add_argument("--turn", type=int, required=name != "join")
        if name in ("create", "join", "advance"):
            sub.add_argument("--role", required=True)
        if name in ("create", "join"):
            # Required (unlike the Codex fork): session name is the only SendMessage-routable
            # address here. thread_id (CLAUDE_CODE_SESSION_ID) authenticates but never routes.
            sub.add_argument("--session", required=True,
                              help="Your exact Claude Code session name from ListAgents")
        if name == "create":
            for option in ("name", "goal", "scope", "assignment"):
                sub.add_argument(f"--{option}", required=True)
            sub.add_argument("--peer", action="append", default=[], help="role=exact-session-name")
            sub.add_argument("--first-role")
        if name == "join":
            sub.add_argument("--resume", action="store_true", help="Explicit continuation of your claimed turn")
        if name == "advance":
            end = sub.add_mutually_exclusive_group(required=True)
            end.add_argument("--to")
            end.add_argument("--pause", metavar="REASON")
            end.add_argument("--complete", action="store_true")
            sub.add_argument("--summary", required=True)
            sub.add_argument("--assignment")
            sub.add_argument("--artifact", action="append", default=[])
        if name in ("pause", "resume"):
            sub.add_argument("--reason", required=True, help="Actual owner instruction or resolved blocker")
        if name == "notify":
            sub.add_argument("--retry-uncertain", action="store_true", help="One investigated retry, never a loop")
        if name == "notify-sent":
            sub.add_argument("--attempt-id", required=True)
            sub.add_argument("--status", required=True, choices=["queued", "uncertain"])
            sub.add_argument("--error")
    return root


def main():
    args = parser().parse_args()
    path = Path(args.table).resolve()
    try:
        if args.command == "notify":
            result = notify(args, path)
        elif args.command == "notify-sent":
            result = notify_sent(args, path)
        else:
            with locked(path):
                if args.command == "create":
                    result = {"result": "created", "table": create(args, path)}
                else:
                    content, state = read_table(path)
                    if args.command == "status":
                        result = {"table": state}
                    else:
                        result = {"result": change(args, state, path), "table": state}
                        write_table(path, content, state)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, IndexError) as exc:
        print(json.dumps({"error": str(exc)}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
