---
name: pr-review
description: Perform a thorough, line-by-line GitHub Pull Request review and post inline comments plus a final verdict using the gh CLI. Use when asked to 'review a PR', given a GitHub PR URL or number, or given a git diff that needs review. Not for ordinary solo code review of uncommitted local changes with no PR, for merging, or for pushing code.
---

# PR Review

Perform a thorough GitHub Pull Request review: line-by-line inline comments on
changed hunks, plus one summary review with a checklist and a final verdict.
Never push, merge, or edit the PR's code yourself; you only comment and
review.

This is the Codex counterpart to the Claude Code `pr-review-specialist`
subagent. Same priorities, severity taxonomy, and verdict rules; different
mechanics, because Codex reviews through the `gh` CLI directly rather than
through a GitHub MCP server and a separately sandboxed subagent.

## Identify the target

Extract the PR from a direct URL (`owner/repo#pull_number`), an
`org/repo#number` reference, or ask for clarification if ambiguous. Confirm
`gh auth status` succeeds before starting; if it does not, tell the user
instead of guessing at credentials.

## Fetch the diff and context

```bash
gh pr view <number> --repo <owner/repo> --json title,body,baseRefName,headRefName,commits
gh pr diff <number> --repo <owner/repo>
gh pr view <number> --repo <owner/repo> --json files --jq '.files[].path'
```

Read each changed file's surrounding context (±10-20 lines beyond the hunk),
not just the diff lines, before judging correctness.

## Review priority order

1. Correctness and edge cases
1a. Following established repo patterns
1b. Codebase pollution: not removing deprecated code, stray comments,
    "enhanced" duplicate files instead of updating the real one, not deleting
    dead files
1c. Accidentally removed or overwritten necessary code
2. Security (injection/XSS/SSRF/secrets)
3. Concurrency & resource safety
4. Error handling & logging
5. Performance
6. API and backward compatibility
7. Tests
8. Documentation

## Severity taxonomy

- **BLOCKER**: must fix before merge (security vulnerabilities, data loss
  risks, critical bugs)
- **MAJOR**: should fix (significant issues, poor error handling, performance
  problems)
- **MINOR**: consider fixing (code quality, maintainability, minor
  optimizations)
- **NIT**: optional polish (naming, formatting, style preferences)

## Post inline comments

Use the GitHub API for inline comments bound to exact file/line/side, since
`gh pr review` alone cannot attach per-line comments:

```bash
gh api repos/<owner>/<repo>/pulls/<number>/comments \
  -f body='**MAJOR**: <one-sentence rationale>

```suggestion
<replacement code>
```' \
  -f commit_id="$(gh pr view <number> --repo <owner/repo> --json headRefOid --jq .headRefOid)" \
  -f path='<file path>' \
  -F line=<line number> \
  -f side=RIGHT
```

Each comment: a severity tag, one-sentence rationale, and a concrete fix or
`suggestion` block when applicable. Batch comments; cap total at ~40,
consolidating related nits into one comment rather than one each.

## Submit the summary review

```bash
gh pr review <number> --repo <owner/repo> --request-changes --body '<summary>'
# or --comment / --approve
```

The summary includes a tally of issues by severity, a checklist
(Correctness/Security/Tests/Performance/Documentation, each ✅ or ❌), and the
final verdict:

- `--request-changes` if any BLOCKER exists
- `--comment` if only MINOR/NITs
- `--approve` if clean

## Safety rules

Never commit, push, or merge. Never include secrets or internal URLs in
comments. If `gh` reports a permission error, tell the user instead of
attempting a workaround credential. If inline comment coordinates cannot be
established (e.g. line moved outside the diff context `gh api` accepts), fall
back to quoting the exact code block in the summary review instead of
guessing a line number.
