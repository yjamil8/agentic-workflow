"""Mechanical instruction-entry failures, using small disposable checkouts."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "check-workflow-instructions.py"
spec = importlib.util.spec_from_file_location("workflow_instructions", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class InstructionChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in checker.DOCUMENTS:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# Instructions\n", encoding="utf-8")
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")

    def write_root(self, content):
        (self.root / "AGENTS.md").write_text(content, encoding="utf-8")

    def run_cli(self):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root)],
                              capture_output=True, text=True, check=False)

    def test_valid_local_anchor_host_path_and_web_link(self):
        self.write_root("# Root\n[ops](strategies/Workspace_Operations.md#instructions)\n"
                        "[host](/home/someone/.codex/skills/agent-table/SKILL.md)\n"
                        "[web](https://example.invalid/guide.md)\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("no semantic or installed-state proof", result.stdout)

    def test_size_boundary_and_utf8_bytes(self):
        self.write_root("x" * checker.ROOT_LIMIT)
        self.assertEqual(checker.check(self.root), [])
        self.write_root("x" * (checker.ROOT_LIMIT - 1) + "é")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("16385 bytes exceeds 16384", result.stdout)

    def test_broken_route_fails_actual_cli(self):
        self.write_root("[required](strategies/missing.md)\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("AGENTS.md:1: missing local route", result.stdout)

    def test_broken_heading_and_reference_destination(self):
        self.write_root("[required][ops]\n\n[ops]: strategies/Workspace_Operations.md#missing\n")
        self.assertTrue(any("AGENTS.md:3: missing heading" in e for e in checker.check(self.root)))

    def test_guide_routes_are_checked(self):
        (self.root / checker.DOCUMENTS[2]).write_text("[required](Missing.md)\n")
        self.assertTrue(any("Workflow_Contribution_Guide.md:1: missing local route" in e
                            for e in checker.check(self.root)))

    def test_pair_is_import_or_symlink_never_copy_or_dangling(self):
        claude = self.root / "CLAUDE.md"
        self.assertEqual(checker.check(self.root), [])
        claude.write_text((self.root / "AGENTS.md").read_text())
        self.assertTrue(any("CLAUDE.md:" in e for e in checker.check(self.root)))
        claude.unlink()
        claude.symlink_to("AGENTS.md")
        self.assertEqual(checker.check(self.root), [])
        claude.unlink()
        claude.symlink_to("missing.md")
        self.assertTrue(any("CLAUDE.md:" in e for e in checker.check(self.root)))

    def test_root_placeholder_links_rebase_to_checkout(self):
        self.write_root("[ok](<agentic-workflow-root>/strategies/Workspace_Operations.md)\n"
                        "[ok2](<agentic-workflow-root>/AGENTS.md)\n")
        self.assertEqual(checker.check(self.root), [])
        self.write_root("[required](<agentic-workflow-root>/strategies/missing.md:12)\n")
        errors = checker.check(self.root)
        self.assertTrue(any("missing local route: <agentic-workflow-root>/strategies/missing.md:12" in e
                            for e in errors), errors)

    def test_fenced_examples_do_not_become_routes(self):
        self.write_root("```markdown\n[example](missing.md)\n```\n"
                        "~~~\n[example](also-missing.md)\n~~~\n")
        self.assertEqual(checker.check(self.root), [])

    def test_root_relative_escape_is_not_an_available_host_dependency(self):
        self.write_root("[required](../AGENTS.md)\n")
        self.assertTrue(any("escapes checkout" in e for e in checker.check(self.root)))

    def test_required_guide_cannot_disappear(self):
        (self.root / checker.DOCUMENTS[1]).unlink()
        self.assertTrue(any("cannot read instruction document" in e for e in checker.check(self.root)))


if __name__ == "__main__":
    unittest.main()
