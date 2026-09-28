#!/usr/bin/env bash
set -euo pipefail

# One-time seed installer: copies this repo's Claude Code and Codex pieces
# into their live install locations (~/.claude/..., ~/.codex/skills/...).
#
# Real copies, never symlinks: Codex's skill discovery silently omits a skill
# whose installed SKILL.md is a symlink (no error, it just never appears).
#
# Any existing file that would change is first backed up next to itself as
# <file>.bak-<timestamp>, so re-running this never destroys a local edit or a
# same-named command/skill you already had.
#
# It also adds a managed block to ~/.claude/CLAUDE.md and ~/.codex/AGENTS.md
# so the toolkit's AGENTS.md rules load in every repository, not just here.
#
# Every `<agentic-workflow-root>` placeholder in an installed markdown file is
# replaced with this checkout's absolute path, so the installed commands and
# skills can find the shared contracts from whatever repo you work in. Move
# the checkout and you must re-run this script.
#
# Usage: scripts/install-local.sh [--dry-run]

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_COMMANDS="$HOME/.claude/commands"
CLAUDE_AGENTS="$HOME/.claude/agents"
CODEX_SKILLS="$HOME/.codex/skills"
STAMP="$(date +%Y%m%d-%H%M%S)"
CHANGED=0
BACKED_UP=0

render() {
  local src="$1"
  if [[ "$src" == *.md ]]; then
    sed "s#<agentic-workflow-root>#$ROOT#g" "$src"
  else
    cat "$src"
  fi
}

install_file() {
  local src="$1" dest="$2"
  local tmp
  tmp="$(mktemp)"
  render "$src" > "$tmp"

  if [[ -f "$dest" && ! -L "$dest" ]] && cmp -s "$tmp" "$dest"; then
    rm -f "$tmp"
    echo "  up to date: $dest"
    return
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    rm -f "$tmp"
    if [[ -e "$dest" || -L "$dest" ]]; then
      echo "  would replace (backing up first): $dest"
    else
      echo "  would install: $dest"
    fi
    return
  fi

  mkdir -p "$(dirname "$dest")"
  if [[ -e "$dest" || -L "$dest" ]]; then
    mv "$dest" "$dest.bak-$STAMP"
    echo "  backed up: $dest -> $dest.bak-$STAMP"
    BACKED_UP=$((BACKED_UP + 1))
  fi
  mv "$tmp" "$dest"
  chmod --reference="$src" "$dest" 2>/dev/null || true
  echo "✓ installed: $dest"
  CHANGED=$((CHANGED + 1))
}

echo "== Claude Code: commands =="
for cmd in "$ROOT"/claude_skills/*/command.md; do
  name="$(basename "$(dirname "$cmd")")"
  install_file "$cmd" "$CLAUDE_COMMANDS/$name.md"
done
install_file "$ROOT/commands/review.md" "$CLAUDE_COMMANDS/review.md"

echo "== Claude Code: agents =="
install_file "$ROOT/agents/pr-review-specialist.md" "$CLAUDE_AGENTS/pr-review-specialist.md"

echo "== Codex: skills =="
while IFS= read -r -d '' src; do
  rel="${src#"$ROOT"/codex_skills/}"
  install_file "$src" "$CODEX_SKILLS/$rel"
done < <(find "$ROOT/codex_skills" -type f -not -path '*/__pycache__/*' -not -name '*.pyc' -print0 | sort -z)

# Global instructions: a managed block inside ~/.claude/CLAUDE.md and
# ~/.codex/AGENTS.md. Everything outside the markers is preserved; re-running
# replaces only the block. Claude imports the live file; Codex has no import
# syntax, so it gets a rendered copy (re-run after editing AGENTS.md).
BEGIN_MARK="<!-- agentic-workflow:begin (managed by scripts/install-local.sh; edits inside are overwritten) -->"
END_MARK="<!-- agentic-workflow:end -->"

install_block() {
  local dest="$1" body_file="$2"
  local tmp
  tmp="$(mktemp)"
  if [[ -f "$dest" ]]; then
    awk -v b="$BEGIN_MARK" -v e="$END_MARK" '
      $0 == b {skip = 1; next}
      $0 == e {skip = 0; next}
      !skip {print}
    ' "$dest" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > "$tmp"
    [[ -s "$tmp" ]] && printf '\n' >> "$tmp"
  fi
  { printf '%s\n' "$BEGIN_MARK"; cat "$body_file"; printf '%s\n' "$END_MARK"; } >> "$tmp"
  install_rendered "$tmp" "$dest"
  rm -f "$tmp"
}

# install_file renders placeholders from a source path; blocks are already
# rendered, so route them through the same backup/compare logic verbatim.
install_rendered() {
  local rendered="$1" dest="$2"
  if [[ -f "$dest" ]] && cmp -s "$rendered" "$dest"; then
    echo "  up to date: $dest"
    return
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  would update (backing up first): $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  if [[ -e "$dest" ]]; then
    cp -p "$dest" "$dest.bak-$STAMP"
    echo "  backed up: $dest -> $dest.bak-$STAMP"
    BACKED_UP=$((BACKED_UP + 1))
  fi
  cp "$rendered" "$dest"
  echo "✓ installed: $dest"
  CHANGED=$((CHANGED + 1))
}

echo "== Global instructions =="
claude_body="$(mktemp)"
cat > "$claude_body" <<EOF
The agentic-workflow toolkit is checked out at $ROOT. Paths in its AGENTS.md
(strategies/, guides/, scripts/) are relative to that directory. A repository's
own CLAUDE.md/AGENTS.md takes precedence wherever it conflicts with these rules.
@$ROOT/AGENTS.md
EOF
install_block "$HOME/.claude/CLAUDE.md" "$claude_body"
rm -f "$claude_body"

codex_body="$(mktemp)"
render "$ROOT/AGENTS.md" > "$codex_body"
install_block "$HOME/.codex/AGENTS.md" "$codex_body"
rm -f "$codex_body"

echo
if [[ "$DRY_RUN" == "1" ]]; then
  echo "== dry run: nothing written =="
else
  echo "== done: $CHANGED file(s) installed, $BACKED_UP backed up =="
  echo "Restart any open Claude Code / Codex session to pick up changes"
  echo "(command/skill lists are read at session start)."
fi
