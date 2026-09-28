#!/usr/bin/env bash
set -euo pipefail

# Prepares a work repository for Agent Tables, implementation plans, and
# runbooks: creates <repo>/agent_tables, <repo>/implementation_plans, and
# <repo>/runbooks, and lists all three in the repo's .git/info/exclude so
# they are never committed by accident.
#
# .git/info/exclude is local to your clone and is itself never committed, so
# this changes nothing your teammates can see. If the team later adopts these
# directories, delete their lines from .git/info/exclude.
#
# Usage: scripts/init-work-repo.sh [path-inside-work-repo]   (default: .)

target="${1:-.}"
repo_root="$(git -C "$target" rev-parse --show-toplevel)"
exclude_file="$(git -C "$repo_root" rev-parse --path-format=absolute --git-common-dir)/info/exclude"

mkdir -p "$repo_root/agent_tables" "$repo_root/implementation_plans" "$repo_root/runbooks" "$(dirname "$exclude_file")"
touch "$exclude_file"

for entry in "/agent_tables/" "/implementation_plans/" "/runbooks/"; do
  if grep -qxF "$entry" "$exclude_file"; then
    echo "  already excluded: $entry"
  else
    printf '%s\n' "$entry" >> "$exclude_file"
    echo "✓ excluded locally: $entry"
  fi
done

echo "Ready: agent_tables/, implementation_plans/, and runbooks/ in $repo_root"
echo "Check: git -C \"$repo_root\" status --short should not list any of them."
