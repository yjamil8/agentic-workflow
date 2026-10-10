#!/usr/bin/env python3
"""Check the root instruction entry and its two routing guides, without app deps.

This checks bytes, the CLAUDE.md pairing and explicit Markdown link
destinations. It does not establish semantic preservation, traverse every
linked document or validate installed/user-local files. Keep links in these
three documents as inline links or reference definitions (not HTML/scripted
navigation); code-fenced examples are not live routes.

The size budget keeps AGENTS.md well inside Codex's default 32 KiB
project_doc_max_bytes limit, past which Codex silently drops the rest of the
file, and keeps the always-loaded global copy small.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT_LIMIT = 16 * 1024
DOCUMENTS = (
    "AGENTS.md",
    "strategies/Workspace_Operations.md",
    "strategies/Workflow_Contribution_Guide.md",
)
# Installed copies replace this placeholder with the checkout path; in the
# source it means the checkout root, so links through it are checked there.
ROOT_PLACEHOLDER = "<agentic-workflow-root>"
ROOT_SENTINEL = "\x02ROOT\x02"


def without_fences(markdown: str) -> str:
    """Retain line numbers while ignoring fenced examples."""
    lines = []
    fence = None
    for line in markdown.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker and fence is None:
            fence = marker.group(1)
            lines.append("")
        elif marker and fence and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
            fence = None
            lines.append("")
        else:
            lines.append(line if fence is None else "")
    return "\n".join(lines)


def destinations(markdown: str):
    """Yield (line, destination) for explicit inline links and definitions."""
    markdown = markdown.replace(ROOT_PLACEHOLDER, ROOT_SENTINEL)
    for number, line in enumerate(without_fences(markdown).splitlines(), 1):
        # Angle-bracket destinations allow spaces; ordinary ones cannot contain
        # whitespace or parentheses. All checked instructions use this form.
        for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[\"'][^\n]*[\"'])?\s*\)", line):
            yield number, (match.group(1) or match.group(2)).replace(ROOT_SENTINEL, ROOT_PLACEHOLDER)
        definition = re.match(r"^\s{0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", line)
        if definition:
            yield number, (definition.group(1) or definition.group(2)).replace(ROOT_SENTINEL, ROOT_PLACEHOLDER)


def heading_ids(markdown: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in without_fences(markdown).splitlines():
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if not match:
            continue
        # GitHub-style slugs for the ordinary text headings in these guides.
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", match.group(1))
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(f"{slug}-{count}" if count else slug)
    anchors.update(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)[\"\']', markdown))
    return anchors


def check(root: Path) -> list[str]:
    root = root.resolve()
    errors = []
    agents = root / "AGENTS.md"
    if not agents.is_file():
        errors.append("AGENTS.md: missing root instruction file")
    elif agents.stat().st_size > ROOT_LIMIT:
        errors.append(f"AGENTS.md: {agents.stat().st_size} bytes exceeds {ROOT_LIMIT}-byte limit")

    claude = root / "CLAUDE.md"
    if claude.is_symlink():
        paired = agents.is_file() and claude.resolve() == agents.resolve()
    else:
        try:
            paired = claude.read_text(encoding="utf-8").strip() == "@AGENTS.md"
        except (OSError, UnicodeError):
            paired = False
    if not paired:
        errors.append("CLAUDE.md: must contain exactly @AGENTS.md or be a working symlink to AGENTS.md")

    for relative in DOCUMENTS:
        document = root / relative
        try:
            markdown = document.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative}: cannot read instruction document: {exc}")
            continue
        for number, raw in destinations(markdown):
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc:
                continue
            path = unquote(parsed.path)
            # Existing editor-style file links may include a line suffix.
            path = re.sub(r":\d+$", "", path)
            if path.startswith(ROOT_PLACEHOLDER):
                target = root / path[len(ROOT_PLACEHOLDER):].lstrip("/")
            elif Path(path).is_absolute() or path.startswith("~/"):
                continue  # Explicit host-only location, not repository evidence.
            else:
                target = document.parent / path if path else document
            target = target.resolve()
            if not target.is_relative_to(root):
                errors.append(f"{relative}:{number}: local route escapes checkout: {raw}")
                continue
            if not target.exists():
                errors.append(f"{relative}:{number}: missing local route: {raw}")
                continue
            if parsed.fragment and target.suffix.lower() == ".md":
                try:
                    anchors = heading_ids(target.read_text(encoding="utf-8"))
                except (OSError, UnicodeError) as exc:
                    errors.append(f"{relative}:{number}: cannot read target {raw}: {exc}")
                    continue
                if unquote(parsed.fragment) not in anchors:
                    errors.append(f"{relative}:{number}: missing heading in local route: {raw}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="root checkout to inspect (default: this script's checkout)")
    args = parser.parse_args()
    errors = check(args.root)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"PASS root instructions: <= {ROOT_LIMIT} bytes, CLAUDE.md pairing, explicit local routes")
    print("Scope: root and two routing guides only; no semantic or installed-state proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
