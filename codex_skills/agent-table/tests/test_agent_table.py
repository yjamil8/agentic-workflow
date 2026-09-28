"""Disposable-table tests. All queue calls are mocked; no live chats are contacted."""

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


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "agent_table.py"
SPEC = importlib.util.spec_from_file_location("agent_table", SCRIPT)
agent_table = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent_table)
A, B, C = (str(uuid.uuid4()) for _ in range(3))


class AgentTableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent-table-test-")
        self.addCleanup(self.temp.cleanup)
        self.table = Path(self.temp.name) / "TABLE.md"
        self.call("create", "--name", "demo", "--goal", "Owner goal", "--scope", "Local only",
                  "--role", "reviewer", "--peer", "implementer=implementer-big",
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

    def notify_args(self, *options):
        return agent_table.parser().parse_args(["notify", "--table", str(self.table),
                                          "--thread", A, *options])

    def test_create_cannot_overwrite_existing_table(self):
        before = self.table.read_bytes()
        self.call("create", "--name", "other", "--goal", "no", "--scope", "no",
                  "--role", "reviewer", "--assignment", "no", success=False)
        self.assertEqual(before, self.table.read_bytes())

    def test_join_binds_invited_name_and_duplicate_does_not_work(self):
        self.assertEqual(self.join()["result"], "claimed")
        self.assertEqual(self.state()["participants"]["implementer"]["thread_id"], B)
        self.assertEqual(self.join()["result"], "already_claimed")
        self.assertEqual(self.call("join", "--role", "implementer", "--resume", thread=B)["result"], "resumed")

    def test_invitation_and_occupied_seat_do_not_guess_identity(self):
        self.call("join", "--role", "implementer", "--session", "almost-the-name", thread=B, success=False)
        self.join()
        self.call("join", "--role", "implementer", "--session", "implementer-big", thread=C, success=False)

    def test_unassigned_role_can_join_standby_without_changing_turn(self):
        self.assertEqual(self.call("join", "--role", "qa", thread=C)["result"], "standby")
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
        self.assertEqual(self.call("join", "--role", "reviewer", *self.identity())["result"], "claimed")

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
        with patch.object(agent_table.subprocess, "run") as transport:
            self.assertEqual(agent_table.notify(self.notify_args(), self.table)["result"], "not_sent")
            transport.assert_not_called()

    def test_concurrent_registration_preserves_all_participants(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(self.call, "join", "--role", "implementer", "--session", "implementer-big", thread=B),
                    pool.submit(self.call, "join", "--role", "qa", thread=C)]
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
        self.call("join", "--role", "qa", thread=C)
        self.join()
        self.advance("--to", "reviewer", "--assignment", "Review")
        self.call("join", "--role", "reviewer", *self.identity())
        self.call("advance", "--role", "reviewer", *self.identity(), "--to", "qa",
                  "--assignment", "Check the affected journey", "--summary", "Candidate reviewed")
        self.call("join", "--role", "qa", *self.identity(), thread=C)
        self.call("advance", "--role", "qa", *self.identity(), "--complete",
                  "--summary", "Requested journey passed; no deployment authorized", thread=C)
        self.assertEqual((self.state()["turn"], self.state()["state"]), (4, "complete"))

    def test_notifications_are_once_only_and_use_argument_array(self):
        queue_id = str(uuid.uuid4())
        accepted = subprocess.CompletedProcess([], 0, f"Queued message {queue_id} for thread {B}.\n", "")
        with patch.object(agent_table.subprocess, "run", return_value=accepted) as transport:
            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = [pool.submit(agent_table.notify, self.notify_args(), self.table) for _ in range(2)]
                for job in jobs:
                    job.result()
            transport.assert_called_once()
            args, kwargs = transport.call_args
            self.assertEqual(args[0][:4], ["codex", "queue", "--thread", "implementer-big"])
            self.assertIn(self.state()["table_id"], args[0][5])
            self.assertNotIn("shell", kwargs)
            self.assertEqual(self.state()["notification"]["queue_id"], queue_id)
            self.assertEqual(self.state()["notification"]["status"], "queued")
            agent_table.notify(self.notify_args("--retry-uncertain"), self.table)
            transport.assert_called_once()
        self.join()
        self.assertEqual(self.state()["notification"]["status"], "received")

    def test_uuid_is_used_after_binding(self):
        self.join()
        self.call("pause", *self.identity(), "--reason", "Owner pause")
        self.call("resume", *self.identity(), "--reason", "Owner resumed")
        with patch.object(agent_table.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as transport:
            agent_table.notify(self.notify_args(), self.table)
            self.assertEqual(transport.call_args.args[0][3], B)

    def test_uncertain_transport_is_not_automatically_retried(self):
        with patch.object(agent_table.subprocess, "run", side_effect=subprocess.TimeoutExpired("codex", 25)) as transport:
            self.assertEqual(agent_table.notify(self.notify_args(), self.table)["status"], "uncertain")
            agent_table.notify(self.notify_args(), self.table)
            transport.assert_called_once()
            agent_table.notify(self.notify_args("--retry-uncertain"), self.table)
            self.assertEqual(transport.call_count, 2)

    def test_pause_during_queue_does_not_get_overwritten_by_acceptance(self):
        def delayed_acceptance(*_args, **_kwargs):
            self.call("pause", *self.identity(), "--reason", "Owner stop during notification")
            return subprocess.CompletedProcess([], 0, "", "")
        real_run = subprocess.run
        def route(command, **kwargs):
            return delayed_acceptance() if command[0] == "codex" else real_run(command, **kwargs)
        with patch.object(agent_table.subprocess, "run", side_effect=route):
            agent_table.notify(self.notify_args(), self.table)
        self.assertEqual(self.state()["state"], "paused")
        self.assertEqual(self.state()["notification"]["status"], "none")

    def test_receipt_during_queue_does_not_get_reverted_to_queued(self):
        real_run = subprocess.run
        def route(command, **kwargs):
            if command[0] != "codex":
                return real_run(command, **kwargs)
            self.join()
            return subprocess.CompletedProcess([], 0, "", "")
        with patch.object(agent_table.subprocess, "run", side_effect=route):
            agent_table.notify(self.notify_args(), self.table)
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
        self.call("join", "--role", "reviewer", success=False)
        self.assertEqual(self.table.read_bytes(), before)

    def test_own_identity_uses_environment_not_session_guessing(self):
        args = agent_table.parser().parse_args(["join", "--table", str(self.table), "--role", "reviewer"])
        with patch.dict(os.environ, {"CODEX_THREAD_ID": A}):
            self.assertEqual(agent_table.own_thread(args), A)
        with patch.dict(os.environ, {"CODEX_THREAD_ID": ""}):
            with self.assertRaises(ValueError):
                agent_table.own_thread(args)


if __name__ == "__main__":
    unittest.main()
