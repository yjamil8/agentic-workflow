#!/usr/bin/env bash
set -euo pipefail

# Surveys every registered git worktree across a set of repos and reports
# which ones are safe to remove: the checked-out commit is already contained
# in the repo's origin/main (or $DEFAULT_BRANCH), and the worktree (plus any
# nested repo inside it) has no uncommitted or untracked changes.
#
# WHY THIS EXISTS: AGENTS.md already requires removing a workstream's
# worktrees in the same session a PR merges, but that step is purely
# self-reported -- nothing lets anyone check later whether it actually
# happened. This script makes that state observable on demand instead of
# relying on the merging agent's memory.
#
# This script only REPORTS. It never removes anything. Removal still follows
# the full work-loss-prevention checklist in AGENTS.md's Collaboration Rules
# (prove containment in origin/main, check nested repos, grep for inbound
# path references before trusting a worktree's *path* is unneeded, etc).
#
# Configure the repo list for your workspace, either by exporting
# WORKTREE_REPOS as a space-separated list of absolute repo paths, or by
# editing the default below.

if [[ -n "${WORKTREE_REPOS:-}" ]]; then
  # shellcheck disable=SC2206
  REPOS=($WORKTREE_REPOS)
else
  REPOS=(
    "$PWD"
  )
fi

DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
DO_FETCH="${DO_FETCH:-1}"

for repo in "${REPOS[@]}"; do
  [[ -d "$repo/.git" ]] || continue
  echo "== $repo =="
  (
    cd "$repo"
    if [[ "$DO_FETCH" == "1" ]]; then
      git fetch origin "$DEFAULT_BRANCH" --quiet 2>/dev/null || true
    fi
    primary="$(git rev-parse --show-toplevel)"

    path=""
    head=""
    branch=""
    prunable="no"

    flush() {
      [[ -z "$path" ]] && return
      if [[ "$path" == "$primary" ]]; then
        path=""; head=""; branch=""; prunable="no"
        return
      fi
      if [[ "$prunable" == "yes" || ! -d "$path" ]]; then
        echo "  PRUNABLE (path missing): $path"
        path=""; head=""; branch=""; prunable="no"
        return
      fi

      local merged="no" dirty="no" nested="clean"
      if [[ -n "$head" ]] && git merge-base --is-ancestor "$head" "origin/$DEFAULT_BRANCH" 2>/dev/null; then
        merged="yes"
      fi
      if [[ -n "$(git -C "$path" status --short --untracked-files=all 2>/dev/null)" ]]; then
        dirty="yes"
      fi
      while IFS= read -r nested_git; do
        nested_dir="$(dirname "$nested_git")"
        [[ "$nested_dir" == "$path" ]] && continue
        if [[ -n "$(git -C "$nested_dir" status --short --untracked-files=all 2>/dev/null)" ]]; then
          nested="dirty: $nested_dir"
        fi
      done < <(find "$path" -mindepth 2 -maxdepth 3 -name ".git" 2>/dev/null)

      local label="${branch:-detached@${head:0:7}}"
      if [[ "$merged" == "yes" && "$dirty" == "no" && "$nested" == "clean" ]]; then
        echo "  SAFE TO REMOVE: $path [$label]"
      else
        echo "  NEEDS REVIEW (merged=$merged dirty=$dirty nested=$nested): $path [$label]"
      fi
      path=""; head=""; branch=""; prunable="no"
    }

    while IFS= read -r line; do
      case "$line" in
        worktree\ *) flush; path="${line#worktree }" ;;
        HEAD\ *) head="${line#HEAD }" ;;
        branch\ *) branch="${line#branch refs/heads/}" ;;
        detached) branch="" ;;
        prunable*) prunable="yes" ;;
        "") ;;
      esac
    done < <(git worktree list --porcelain)
    flush
  )
done

echo
echo "SAFE TO REMOVE proves the worktree's CONTENT is not needed (merged, clean)."
echo "It does not prove the PATH is unneeded: relative references from other"
echo "worktrees can still resolve through it (see AGENTS.md's Collaboration"
echo "Rules note on this, and add a note here for any repo in your workspace"
echo "with the same nested-reference hazard). Grep the workspace for inbound"
echo "references before removing, and follow the full checklist there, not"
echo "just this script."
