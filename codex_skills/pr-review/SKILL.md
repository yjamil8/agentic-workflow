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

## Submit one review with all inline comments

Post everything as a single review, not one API call per comment: separate
calls notify the PR author once per comment. Write the review payload to a
temporary JSON file (this also avoids shell-quoting problems with multi-line
bodies and `suggestion` fences), then submit it once:

~~~bash
HEAD_SHA="$(gh pr view <number> --repo <owner/repo> --json headRefOid --jq .headRefOid)"
cat > /tmp/pr-review.json <<'JSON'
{
  "commit_id": "<HEAD_SHA>",
  "event": "COMMENT",
  "body": "<summary: severity tally, checklist, verdict>",
  "comments": [
    {
      "path": "src/example.ts",
      "line": 42,
      "side": "RIGHT",
      "body": "**MAJOR**: <one-sentence rationale>\n\n```suggestion\n<replacement code>\n```"
    }
  ]
}
JSON
sed -i "s/<HEAD_SHA>/$HEAD_SHA/" /tmp/pr-review.json
gh api repos/<owner>/<repo>/pulls/<number>/reviews --method POST --input /tmp/pr-review.json
rm -f /tmp/pr-review.json
~~~

Each comment: a severity tag, one-sentence rationale, and a concrete fix or
`suggestion` block when applicable. Cap the review at ~40 comments,
consolidating related nits into one comment rather than one each. `line`
must fall inside a hunk of the PR diff (use `side: "LEFT"` for a deleted
line); GitHub rejects the whole review with HTTP 422 otherwise, so move any
comment that cannot be anchored into the summary body with a quoted code
block instead of guessing a line.

## Summary and verdict

The `body` includes a tally of issues by severity, a checklist
(Correctness/Security/Tests/Performance/Documentation, each ✅ or ❌), and the
final verdict, set through `event`:

- `REQUEST_CHANGES` if any BLOCKER exists
- `COMMENT` if only MINOR/NITs
- `APPROVE` if clean

GitHub does not allow `APPROVE` or `REQUEST_CHANGES` on a PR authored by the
authenticated account. When reviewing your own PR, submit `COMMENT` and state
the intended verdict in the first line of the body.

## Safety rules

Never commit, push, or merge. Never include secrets or internal URLs in
comments. If `gh` reports a permission error, tell the user instead of
attempting a workaround credential. If inline comment coordinates cannot be
established, fall back to quoting the exact code block in the summary body
instead of guessing a line number.
