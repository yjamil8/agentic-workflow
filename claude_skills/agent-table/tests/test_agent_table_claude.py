"""Disposable-table tests. No live sessions are contacted; SendMessage is out of process."""

from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "agent_table_claude.py"
SPEC = importlib.util.spec_from_file_location("agent_table_claude", SCRIPT)
agent_table = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent_table)
A, B, C = (str(uuid.uuid4()) for _ in range(3))


class AgentTableClaudeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent-table-claude-test-")
        self.addCleanup(self.temp.cleanup)
        self.table = Path(self.temp.name) / "TABLE.md"
        self.call("create", "--name", "demo", "--goal", "Owner goal", "--scope", "Local only",
                  "--role", "reviewer", "--session", "reviewer-big", "--peer", "implementer=implementer-big",
                  "--first-role", "implementer", "--assignment", "Implement the authorized fix")

    def call(self, command, *options, thread=A, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), command, "--table", str(self.table),
                                 "--thread", thread, *options], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def state(self):
        return agent_table.read_table(self.table)[1]

    def identity(self):
        state = self.state()
        return ["--table-id", state["table_id"], "--turn", str(state["turn"])]

    def join(self, **kwargs):
        return self.call("join", "--role", "implementer", "--session", "implementer-big",
                         *self.identity(), thread=B, **kwargs)

    def advance(self, *options, **kwargs):
        return self.call("advance", "--role", "implementer", *self.identity(),
                         "--summary", "Affected candidate ready", *options, thread=B, **kwargs)

    def notify_args(self, *options, thread=A):
        return agent_table.parser().parse_args(["notify", "--table", str(self.table),
                                          "--thread", thread, *options])

    def ack(self, result, status="queued", thread=A, error=None, **kwargs):
        options = ["--table-id", result["table_id"], "--turn", str(result["turn"]),
                   "--attempt-id", result["attempt_id"], "--status", status]
        if error is not None:
            options += ["--error", error]
        return self.call("notify-sent", *options, thread=thread, **kwargs)

    def test_create_cannot_overwrite_existing_table(self):
        before = self.table.read_bytes()
        self.call("create", "--name", "other", "--goal", "no", "--scope", "no",
                  "--role", "reviewer", "--session", "other-session", "--assignment", "no", success=False)
        self.assertEqual(before, self.table.read_bytes())

    def test_join_binds_invited_name_and_duplicate_does_not_work(self):
        self.assertEqual(self.join()["result"], "claimed")
        self.assertEqual(self.state()["participants"]["implementer"]["thread_id"], B)
        self.assertEqual(self.join()["result"], "already_claimed")
        self.assertEqual(self.call("join", "--role", "implementer", "--session", "implementer-big",
                                   "--resume", thread=B)["result"], "resumed")

    def test_invitation_and_occupied_seat_do_not_guess_identity(self):
        self.call("join", "--role", "implementer", "--session", "almost-the-name", thread=B, success=False)
        self.join()
        self.call("join", "--role", "implementer", "--session", "implementer-big", thread=C, success=False)

    def test_unassigned_role_can_join_standby_without_changing_turn(self):
        self.assertEqual(self.call("join", "--role", "qa", "--session", "qa-big", thread=C)["result"], "standby")
        self.assertEqual(self.state()["turn"], 1)
        self.assertEqual(self.state()["current_role"], "implementer")

    def test_wrong_generation_or_turn_cannot_bind_or_claim(self):
        before = self.table.read_bytes()
        for identity in (["--table-id", str(uuid.uuid4()), "--turn", "1"],
                         ["--table-id", self.state()["table_id"], "--turn", "2"]):
            self.call("join", "--role", "implementer", "--session", "implementer-big",
                      *identity, thread=B, success=False)
        self.assertEqual(before, self.table.read_bytes())

    def test_artifact_first_and_only_claimed_role_advances(self):
        self.advance("--to", "reviewer", "--assignment", "Review", success=False)
        self.join()
        self.advance("--to", "reviewer", "--assignment", "Review",
                     "--artifact", "missing.md", success=False)
        artifact = self.table.parent / "candidate.md"
        artifact.write_text("Exact candidate and affected evidence\n")
        self.advance("--to", "reviewer", "--assignment", "Review", "--artifact", "candidate.md")
        state = self.state()
        self.assertEqual((state["turn"], state["current_role"], state["state"]), (2, "reviewer", "ready"))
        self.assertEqual(state["artifacts"], [str(artifact)])
        self.assertEqual(self.call("join", "--role", "reviewer", "--session", "reviewer-big",
                                   *self.identity())["result"], "claimed")

    def test_owner_pause_invalidates_old_work_and_resume_is_a_new_turn(self):
        self.join()
        old = self.identity()
        self.call("pause", *old, "--reason", "Owner says stop")
        self.call("advance", "--role", "implementer", *old, "--complete", "--summary", "stale",
                  thread=B, success=False)
        self.assertEqual(self.join()["result"], "paused")
        self.call("resume", *self.identity(), "--reason", "Owner explicitly resumed")
        self.assertEqual(self.state()["turn"], 3)
        self.assertEqual(self.join()["result"], "claimed")

    def test_complete_cannot_be_reopened_by_a_notification_or_pause(self):
        self.join()
        self.advance("--complete")
        self.assertEqual(self.join()["result"], "complete")
        self.call("pause", *self.identity(), "--reason", "invalid", success=False)
        self.assertEqual(agent_table.notify(self.notify_args(), self.table)["result"], "not_sent")

    def test_concurrent_registration_preserves_all_participants(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(self.call, "join", "--role", "implementer", "--session", "implementer-big", thread=B),
                    pool.submit(self.call, "join", "--role", "qa", "--session", "qa-big", thread=C)]
            for job in jobs:
                job.result()
        self.assertEqual(len(self.state()["participants"]), 3)
        self.assertEqual(self.state()["participants"]["qa"]["thread_id"], C)

    def test_concurrent_handoffs_have_one_winner(self):
        self.join()
        command = [sys.executable, str(SCRIPT), "advance", "--table", str(self.table),
                   "--thread", B, "--role", "implementer", *self.identity(),
                   "--to", "reviewer", "--assignment", "Review", "--summary", "Done"]
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(subprocess.run, command, capture_output=True) for _ in range(2)]
            self.assertEqual(sorted(job.result().returncode for job in jobs), [0, 1])
        self.assertEqual(self.state()["turn"], 2)

    def test_three_roles_complete_a_workflow_without_owner_activation(self):
        self.call("join", "--role", "qa", "--session", "qa-big", thread=C)
        self.join()
        self.advance("--to", "reviewer", "--assignment", "Review")
        self.call("join", "--role", "reviewer", "--session", "reviewer-big", *self.identity())
        self.call("advance", "--role", "reviewer", *self.identity(), "--to", "qa",
                  "--assignment", "Check the affected journey", "--summary", "Candidate reviewed")
        self.call("join", "--role", "qa", "--session", "qa-big", *self.identity(), thread=C)
        self.call("advance", "--role", "qa", *self.identity(), "--complete",
                  "--summary", "Requested journey passed; no deployment authorized", thread=C)
        self.assertEqual((self.state()["turn"], self.state()["state"]), (4, "complete"))

    def test_notifications_are_once_only_and_use_two_phase_handoff(self):
        first = agent_table.notify(self.notify_args(), self.table)
        self.assertEqual(first["result"], "ready_to_send")
        self.assertEqual(first["target"], "implementer-big")
        self.assertIn(self.state()["table_id"], first["message"])
        self.assertEqual(self.state()["notification"]["status"], "sending")
        # A second concurrent notify before notify-sent must not re-send.
        second = agent_table.notify(self.notify_args(), self.table)
        self.assertEqual(second["result"], "uncertain; inspect before an explicit retry")
        self.assertEqual(self.ack(first)["result"], "recorded")
        self.assertEqual(self.state()["notification"]["status"], "queued")
        self.join()
        self.assertEqual(self.state()["notification"]["status"], "received")

    def test_session_name_stays_the_routing_target_after_binding(self):
        # Unlike the Codex fork, thread_id (CLAUDE_CODE_SESSION_ID) is never routable via
        # SendMessage; the invited session name must remain the target even once bound.
        self.join()
        self.call("pause", *self.identity(), "--reason", "Owner pause")
        self.call("resume", *self.identity(), "--reason", "Owner resumed")
        result = agent_table.notify(self.notify_args(), self.table)
        self.assertEqual(result["target"], "implementer-big")
        self.assertNotEqual(result["target"], B)

    def test_uncertain_notification_is_not_automatically_retried(self):
        first = agent_table.notify(self.notify_args(), self.table)
        self.assertEqual(self.ack(first, status="uncertain", error="SendMessage timed out")["result"], "recorded")
        self.assertEqual(self.state()["notification"]["status"], "uncertain")
        self.assertEqual(agent_table.notify(self.notify_args(), self.table)["result"],
                         "uncertain; inspect before an explicit retry")
        retried = agent_table.notify(self.notify_args("--retry-uncertain"), self.table)
        self.assertEqual(retried["result"], "ready_to_send")
        self.assertNotEqual(retried["attempt_id"], first["attempt_id"])

    def test_pause_during_notify_does_not_get_overwritten_by_late_ack(self):
        first = agent_table.notify(self.notify_args(), self.table)
        self.call("pause", *self.identity(), "--reason", "Owner stop during notification")
        self.assertEqual(self.ack(first)["result"], "stale; table advanced before acknowledgement")
        self.assertEqual(self.state()["state"], "paused")
        self.assertEqual(self.state()["notification"]["status"], "none")

    def test_receipt_during_notify_does_not_get_reverted_to_queued(self):
        first = agent_table.notify(self.notify_args(), self.table)
        self.join()
        self.assertEqual(self.ack(first)["result"], "stale; table advanced before acknowledgement")
        self.assertEqual(self.state()["notification"]["status"], "received")
        self.assertEqual(self.state()["state"], "working")

    def test_preserves_notes_outside_managed_block(self):
        with self.table.open("a") as output:
            output.write("\nOwner note: preserve this.\n")
        self.join()
        self.assertTrue(self.table.read_text().endswith("\nOwner note: preserve this.\n"))

    def test_existing_legacy_table_is_not_rewritten(self):
        self.table.write_text("# Existing table\n\n- Turn: 8\n")
        before = self.table.read_bytes()
        self.call("join", "--role", "reviewer", "--session", "reviewer-big", success=False)
        self.assertEqual(self.table.read_bytes(), before)

    def test_own_identity_uses_environment_not_session_guessing(self):
        args = agent_table.parser().parse_args(["join", "--table", str(self.table), "--role", "reviewer",
                                          "--session", "reviewer-big"])
        with patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": A}):
            self.assertEqual(agent_table.own_thread(args), A)
        with patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": ""}):
            with self.assertRaises(ValueError):
                agent_table.own_thread(args)


if __name__ == "__main__":
    unittest.main()
