#!/usr/bin/env bash
set -euo pipefail

# One-time seed installer: copies this repo's Claude Code and Codex pieces
# into their live install locations (~/.claude/..., ~/.codex/skills/...).
#
# This is a COPY, not a symlink, on purpose: Codex's skill discovery silently
# omits a skill whose installed SKILL.md is a symlink (no error, it just
# never appears in a fresh session's skill list). Since this repo is a
# one-time seed rather than a continuously synced mirror, plain copies are
# correct here; re-run this script after editing the repo to push updates,
# there is no automatic live sync.
#
# Usage: scripts/install-local.sh [--dry-run]

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_COMMANDS="$HOME/.claude/commands"
CLAUDE_AGENTS="$HOME/.claude/agents"
CODEX_SKILLS="$HOME/.codex/skills"

install_file() {
  local src="$1" dest="$2" templatize="${3:-0}"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  would install: $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  if [[ "$templatize" == "1" ]]; then
    sed "s#<agentic-workflow-root>#$ROOT#g" "$src" > "$dest"
  else
    cp "$src" "$dest"
  fi
  echo "✓ installed: $dest"
}

echo "== Claude Code: commands =="
install_file "$ROOT/claude_skills/rally/command.md" "$CLAUDE_COMMANDS/rally.md" 1
install_file "$ROOT/claude_skills/adversarial-plan-review/command.md" "$CLAUDE_COMMANDS/adversarial-plan-review.md" 1
install_file "$ROOT/commands/review.md" "$CLAUDE_COMMANDS/review.md"

echo "== Claude Code: agents =="
install_file "$ROOT/agents/pr-review-specialist.md" "$CLAUDE_AGENTS/pr-review-specialist.md"

echo "== Codex: skills =="
for skill_dir in "$ROOT"/codex_skills/*/; do
  name="$(basename "$skill_dir")"
  dest_dir="$CODEX_SKILLS/$name"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  would install: $dest_dir/ (from $skill_dir)"
    continue
  fi
  mkdir -p "$dest_dir"
  cp -r "$skill_dir"/. "$dest_dir"/
  # Belt-and-suspenders: guarantee SKILL.md is a real file, never a symlink.
  if [[ -L "$dest_dir/SKILL.md" ]]; then
    echo "✗ $name: SKILL.md installed as a symlink -- fixing"
    real="$(readlink -f "$dest_dir/SKILL.md")"
    rm -f "$dest_dir/SKILL.md"
    cp "$real" "$dest_dir/SKILL.md"
  fi
  echo "✓ installed: $dest_dir"
done

echo
echo "== done =="
echo "Restart any open Claude Code / Codex session to pick up changes"
echo "(command/skill lists are read at session start)."
echo "This repo is a one-time seed, not a live sync: re-run this script"
echo "after editing files here to push updates to the live install."
