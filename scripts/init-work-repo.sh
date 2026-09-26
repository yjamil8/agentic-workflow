#!/usr/bin/env bash
set -euo pipefail

# Prepares a work repository for Agent Tables and implementation plans:
# creates <repo>/agent_tables and <repo>/implementation_plans, and lists both
# in the repo's .git/info/exclude so they are never committed by accident.
#
# .git/info/exclude is local to your clone and is itself never committed, so
# this changes nothing your teammates can see. If the team later adopts these
# directories, delete the two lines from .git/info/exclude.
#
# Usage: scripts/init-work-repo.sh [path-inside-work-repo]   (default: .)

target="${1:-.}"
repo_root="$(git -C "$target" rev-parse --show-toplevel)"
exclude_file="$(git -C "$repo_root" rev-parse --path-format=absolute --git-common-dir)/info/exclude"

mkdir -p "$repo_root/agent_tables" "$repo_root/implementation_plans" "$(dirname "$exclude_file")"
touch "$exclude_file"

for entry in "/agent_tables/" "/implementation_plans/"; do
  if grep -qxF "$entry" "$exclude_file"; then
    echo "  already excluded: $entry"
  else
    printf '%s\n' "$entry" >> "$exclude_file"
    echo "✓ excluded locally: $entry"
  fi
done

echo "Ready: $repo_root/agent_tables and $repo_root/implementation_plans"
echo "Check: git -C \"$repo_root\" status --short should not list either directory."
